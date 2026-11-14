
import requests
import os

url = (
    "https://planetarymaps.usgs.gov/mosaic/"
    "mars2020_trn/CTX/ScienceInvestigationMaps_JPL/"
    "M20_JezeroCrater_CTXortho_mosaic_5m.tif"
)

output = "data/raw/jezero_ctx_ortho.tif"

os.makedirs("data/raw", exist_ok=True)

print("Downloading official USGS CTX orthomosaic...")

response = requests.get(
    url,
    stream=True,
    timeout=120
)

response.raise_for_status()

total = int(response.headers.get("content-length", 0))
downloaded = 0

with open(output, "wb") as file:
    for chunk in response.iter_content(chunk_size=1024 * 1024):
        if chunk:
            file.write(chunk)
            downloaded += len(chunk)

            if total:
                percentage = downloaded / total * 100
                print(
                    f"\rDownloaded: {percentage:.1f}%",
                    end=""
                )

print("\n\nDownload completed!")
print("Saved to:", output)
print("Size:", round(downloaded / (1024 * 1024), 2), "MB")
