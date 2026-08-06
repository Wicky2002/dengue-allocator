"""Ingest the ``colmozzie`` CRAN dataset: the fast-path prototyping source.

``colmozzie`` (Talagala, CC0) holds weekly notified dengue cases and climate
variables for **Colombo district** from 2009 through mid-2014, transcribed from
Epidemiology Unit weekly epidemiological reports. 279 district-weeks, one
district. It is small, permissively licensed, and downloads in seconds, which
makes it the right thing to prototype against before the full 25-district panel
lands.

The package ships its data only as an R ``.rda`` binary, so this module contains
a small, purpose-built reader for R's serialisation format. That is deliberate:
the alternatives (``pyreadr``, ``rpy2``) drag in a compiled toolchain or a full R
installation for one 9 KB file, and both are routine sources of install failure
on Windows. The reader below handles exactly the subset of the format that a
serialised ``data.frame`` uses, and raises loudly on anything else.

Source
------
https://cran.r-project.org/package=colmozzie (archived; fetched from
``src/contrib/Archive/colmozzie/``). Licence: CC0-1.0.

Column mapping to the frozen panel schema
-----------------------------------------
==============  ==================  ======================================
colmozzie       panel               note
==============  ==================  ======================================
``Cases``       ``cases``           notified dengue cases
``Year``+``Week`` ``iso_week``      ISO-8601 week
``PP``          ``rain_mm``         precipitation, mm
``TMAX``        ``tmax``            weekly max temperature, C
``Tm``          ``tmin``            weekly min temperature, C
``H``           ``rh``              relative humidity, %
--              ``population``      from the district registry
--              ``high_risk_flag``  null: colmozzie predates NDCU designations
==============  ==================  ======================================

``TEM``, ``SLP``, ``VV``, ``V`` and ``VM`` (mean temperature, sea-level
pressure, visibility, wind) are not in the panel schema and are dropped.
"""

from __future__ import annotations

import bz2
import gzip
import io
import lzma
import struct
import tarfile
from pathlib import Path
from typing import Any

import pandas as pd

from dengue import config
from dengue.utils.io import IngestError, coerce_panel_schema, download_binary
from dengue.utils.logging import get_logger, log_frame

log = get_logger(__name__)

COLMOZZIE_VERSION = "1.1.1"
COLMOZZIE_URL = (
    f"{config.CRAN_BASE_URL}/src/contrib/Archive/colmozzie/" f"colmozzie_{COLMOZZIE_VERSION}.tar.gz"
)
COLMOZZIE_LICENCE = "CC0-1.0"

#: colmozzie covers Colombo district only.
COLMOZZIE_DISTRICT = "colombo"

#: Documented shape; used as an integrity check, never to synthesise rows.
EXPECTED_ROWS = 279
EXPECTED_COLUMNS = (
    "Cases",
    "Year",
    "Week",
    "TEM",
    "TMAX",
    "Tm",
    "SLP",
    "H",
    "PP",
    "VV",
    "V",
    "VM",
)


# --------------------------------------------------------------------------
# Minimal RData reader
# --------------------------------------------------------------------------

_NILVALUE_SXP = 254
_REFSXP = 255
_SYMSXP = 1
_LISTSXP = 2
_CHARSXP = 9
_LGLSXP = 10
_INTSXP = 13
_REALSXP = 14
_STRSXP = 16
_VECSXP = 19

_NA_INTEGER = -2147483648


class _RDataReader:
    """Byte reader for R's XDR (big-endian) serialisation format."""

    def __init__(self, buf: bytes) -> None:
        self.buf = buf
        self.pos = 0
        self.refs: list[Any] = []

    def read_int(self) -> int:
        value = struct.unpack_from(">i", self.buf, self.pos)[0]
        self.pos += 4
        return int(value)

    def read_double(self) -> float:
        value = struct.unpack_from(">d", self.buf, self.pos)[0]
        self.pos += 8
        return float(value)

    def read_bytes(self, n: int) -> bytes:
        value = self.buf[self.pos : self.pos + n]
        self.pos += n
        return value


def _read_sexp(r: _RDataReader) -> Any:
    """Read one R object. Returns plain Python structures.

    Vectors come back as ``{"data": [...], "attrs": {...}}`` so that a
    data.frame's ``names`` / ``row.names`` attributes survive.
    """
    flags = r.read_int()
    sxp_type = flags & 0xFF
    has_attr = bool((flags >> 9) & 1)
    has_tag = bool((flags >> 10) & 1)

    if sxp_type in (0, _NILVALUE_SXP):
        return None

    if sxp_type == _REFSXP:
        index = flags >> 8
        if index == 0:
            index = r.read_int()
        return r.refs[index - 1]

    if sxp_type == _SYMSXP:
        name = _read_sexp(r)
        r.refs.append(name)
        return name

    if sxp_type == _CHARSXP:
        length = r.read_int()
        if length < 0:  # NA_character_
            return None
        return r.read_bytes(length).decode("utf-8", errors="replace")

    if sxp_type == _LISTSXP:
        # Pairlist node: [attributes] [tag] CAR CDR. Flattened to (tag, value) pairs.
        if has_attr:
            _read_sexp(r)
        tag = _read_sexp(r) if has_tag else None
        car = _read_sexp(r)
        cdr = _read_sexp(r)
        pairs = [(tag, car)]
        if isinstance(cdr, list) and cdr and isinstance(cdr[0], tuple):
            pairs.extend(cdr)
        return pairs

    if sxp_type in (_INTSXP, _LGLSXP):
        n = r.read_int()
        raw = [r.read_int() for _ in range(n)]
        data: list[Any] = [None if v == _NA_INTEGER else v for v in raw]
    elif sxp_type == _REALSXP:
        n = r.read_int()
        data = [r.read_double() for _ in range(n)]
    elif sxp_type in (_STRSXP, _VECSXP):
        n = r.read_int()
        data = [_read_sexp(r) for _ in range(n)]
    else:
        raise IngestError(
            f"colmozzie .rda contains unsupported R SEXP type {sxp_type} at byte {r.pos}. "
            "The upstream file format changed; this reader needs extending."
        )

    attrs: dict[str, Any] = {}
    if has_attr:
        pairs = _read_sexp(r)
        if pairs:
            for tag, value in pairs:
                if tag is not None:
                    attrs[tag] = value

    return {"data": data, "attrs": attrs}


def _decompress(raw: bytes) -> bytes:
    """Decompress an ``.rda``. R's ``save()`` may use gzip, bzip2 or xz."""
    if raw[:2] == b"\x1f\x8b":
        return gzip.decompress(raw)
    if raw[:3] == b"BZh":
        return bz2.decompress(raw)
    if raw[:6] == b"\xfd7zXZ\x00":
        return lzma.decompress(raw)
    return raw  # already uncompressed


def read_rda_dataframe(raw: bytes) -> pd.DataFrame:
    """Parse a serialised R ``data.frame`` from ``.rda`` bytes.

    Parameters
    ----------
    raw:
        Raw ``.rda`` file contents, compressed or not.

    Returns
    -------
    pandas.DataFrame
        The first data.frame in the file, with its original column names.

    Raises
    ------
    IngestError
        If the file is not a recognised RData container or holds no data.frame.
    """
    data = _decompress(raw)
    stream = io.BytesIO(data)

    magic = stream.readline()
    if not magic.startswith(b"RDX"):
        raise IngestError(f"Not an RData file: magic bytes were {magic[:8]!r}")
    fmt = stream.readline()
    if not fmt.startswith(b"X"):
        raise IngestError(
            f"Only XDR-format RData is supported; file declares {fmt!r}. "
            "Re-save with `save(x, file=..., ascii=FALSE)`."
        )

    r = _RDataReader(stream.read())
    version = r.read_int()
    r.read_int()  # R version that wrote the file
    r.read_int()  # minimum R version required
    if version == 3:
        length = r.read_int()
        r.read_bytes(length)  # native encoding string

    top = _read_sexp(r)
    if not isinstance(top, list):
        raise IngestError("RData top level was not a pairlist of named objects")

    for name, obj in top:
        if not isinstance(obj, dict):
            continue
        columns = obj.get("attrs", {}).get("names")
        if columns is None:
            continue
        col_names = columns["data"] if isinstance(columns, dict) else columns
        frame = pd.DataFrame(
            {
                col: (c["data"] if isinstance(c, dict) else c)
                for col, c in zip(col_names, obj["data"], strict=True)
            }
        )
        log.debug("parsed R data.frame %r with shape %s", name, frame.shape)
        return frame

    raise IngestError("No data.frame found in the RData file")


# --------------------------------------------------------------------------
# Ingest
# --------------------------------------------------------------------------


def download(refresh: bool = False) -> Path:
    """Download the colmozzie source tarball to ``data/raw/colmozzie/``."""
    config.ensure_dirs()
    dest = config.RAW_COLMOZZIE / f"colmozzie_{COLMOZZIE_VERSION}.tar.gz"
    return download_binary(COLMOZZIE_URL, dest, refresh=refresh)


def extract_raw_frame(tarball: Path) -> pd.DataFrame:
    """Extract ``data/colmozzie.rda`` from the tarball and parse it."""
    with tarfile.open(tarball, mode="r:gz") as tf:
        member = next((m for m in tf.getmembers() if m.name.endswith(".rda")), None)
        if member is None:
            raise IngestError(f"No .rda file inside {tarball}")
        handle = tf.extractfile(member)
        if handle is None:
            raise IngestError(f"Could not read {member.name} from {tarball}")
        raw = handle.read()

    frame = read_rda_dataframe(raw)

    missing = [c for c in EXPECTED_COLUMNS if c not in frame.columns]
    if missing:
        raise IngestError(
            f"colmozzie schema changed: missing columns {missing}. " f"Got {list(frame.columns)}"
        )
    if len(frame) != EXPECTED_ROWS:
        # Not fatal -- upstream could legitimately extend the series -- but it
        # must be visible, because a silent truncation would look like a dip.
        log.warning(
            "colmozzie row count is %d, expected %d. Upstream data may have changed.",
            len(frame),
            EXPECTED_ROWS,
        )
    return frame


def _iso_week_period(year: int, week: int) -> pd.Period | None:
    """Convert an ISO (year, week) pair to a weekly Period, or None if invalid."""
    try:
        monday = pd.Timestamp.fromisocalendar(int(year), int(week), 1)
    except ValueError:
        # e.g. week 53 in a 52-week year: a genuine upstream data error.
        return None
    return pd.Period(monday, freq=config.WEEK_FREQ)


def normalise(frame: pd.DataFrame) -> pd.DataFrame:
    """Map the raw colmozzie frame onto the frozen panel schema."""
    district = config.get_district(COLMOZZIE_DISTRICT)

    periods = [_iso_week_period(y, w) for y, w in zip(frame["Year"], frame["Week"], strict=True)]
    bad = [
        (y, w)
        for (y, w), p in zip(zip(frame["Year"], frame["Week"], strict=True), periods, strict=True)
        if p is None
    ]
    if bad:
        log.warning("Dropping %d colmozzie rows with invalid ISO year/week: %s", len(bad), bad[:5])

    panel = pd.DataFrame(
        {
            "district_id": COLMOZZIE_DISTRICT,
            "iso_week": periods,
            "cases": frame["Cases"],
            "population": district.population,
            "rain_mm": frame["PP"],
            "tmax": frame["TMAX"],
            "tmin": frame["Tm"],
            "rh": frame["H"],
            # colmozzie predates the NDCU high-risk MOH designations entirely.
            "high_risk_flag": pd.NA,
        }
    )
    panel = panel[panel["iso_week"].notna()]

    duplicated = panel.duplicated(subset=["district_id", "iso_week"]).sum()
    if duplicated:
        log.warning("colmozzie has %d duplicate district-weeks; keeping the first", duplicated)
        panel = panel.drop_duplicates(subset=["district_id", "iso_week"], keep="first")

    return coerce_panel_schema(panel)


def load(refresh: bool = False) -> pd.DataFrame:
    """Download, parse and normalise colmozzie into the panel schema.

    Returns
    -------
    pandas.DataFrame
        A single-district panel conforming to
        :data:`dengue.config.PANEL_DTYPES`.

    Raises
    ------
    IngestError
        On any download or parse failure. Never returns partial or invented data.
    """
    log.info("colmozzie: fetching %s (licence %s)", COLMOZZIE_URL, COLMOZZIE_LICENCE)
    tarball = download(refresh=refresh)
    raw_frame = extract_raw_frame(tarball)
    log.info(
        "colmozzie: parsed raw frame  rows=%d  cols=%d  years=[%s .. %s]",
        len(raw_frame),
        raw_frame.shape[1],
        raw_frame["Year"].min(),
        raw_frame["Year"].max(),
    )

    panel = normalise(raw_frame)
    log_frame(log, panel, "colmozzie:normalised")
    return panel


def main() -> None:  # pragma: no cover - CLI entry point
    config.ensure_dirs()
    panel = load()
    out = config.INTERIM_DIR / "colmozzie_panel.parquet"
    to_write = panel.copy()
    to_write["iso_week"] = to_write["iso_week"].dt.start_time.dt.strftime("%Y-%m-%d")
    to_write.to_parquet(out, index=False)
    log.info("colmozzie: wrote %s", out)


if __name__ == "__main__":  # pragma: no cover
    main()
