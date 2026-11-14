from enum import Enum


class Device(str, Enum):
    kindle_paperwhite2 = "kindle_paperwhite2"
    kindle_paperwhite3 = "kindle_paperwhite3"
    kindle_paperwhite5 = "kindle_paperwhite5"
    kindle_paperwhite6 = "kindle_paperwhite6"
    kindle_voyage = "kindle_voyage"
    kindle_oasis = "kindle_oasis"
    kindle_basic = "kindle_basic"
    kindle_basic11 = "kindle_basic11"


# Screen resolution in portrait orientation, as (width, height).
# Only kindle_paperwhite2 has been tested end to end; the others come from
# published device specs.
SIZE_MAP: dict[Device, tuple[int, int]] = {
    Device.kindle_paperwhite2: (758, 1024),  # Paperwhite 1 & 2 (2012, 2013)
    Device.kindle_paperwhite3: (1072, 1448),  # Paperwhite 3 & 4 (2015, 2018)
    Device.kindle_paperwhite5: (1236, 1648),  # Paperwhite 5 (2021)
    Device.kindle_paperwhite6: (1264, 1680),  # Paperwhite 12th gen (2024)
    Device.kindle_voyage: (1072, 1448),
    Device.kindle_oasis: (1264, 1680),  # Oasis 2 & 3
    Device.kindle_basic: (600, 800),  # Kindle 10th gen and older
    Device.kindle_basic11: (1072, 1448),  # Kindle 11th gen (2022)
}
