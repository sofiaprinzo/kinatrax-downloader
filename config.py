import os

from dotenv import load_dotenv


load_dotenv()


class Config:
    API_URL = os.getenv("KINATRAX_BASE_URL", "https://explorer-api.kinatrax.com").rstrip("/")
    API_PATH = os.getenv("KINATRAX_API_PATH", "/ktx_s3").strip("/")
    API_KEY = os.getenv("KINATRAX_API_KEY")
    LIST_PATH = "Data/CPS/2026/"
    TEST_FILE_PATH = (
        "Data/CPS/2026/2026_04_07_16_13_35/Pitching/2026_04_07_18_18_51_Cal_Poly_Mustangs_41_Sean_McGrath_Home/McGrath_Slider_80.1_1.4_-17.8_TM_Metadata.txt"
    )

config = Config()
