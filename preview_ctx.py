
import rasterio
import matplotlib.pyplot as plt
from rasterio.enums import Resampling

path = "data/processed/jezero_ctx_aligned.tif"

with rasterio.open(path) as src:
    image = src.read(
        1,
        out_shape=(700, round(src.width * 700 / src.height)),
        masked=True,
        resampling=Resampling.nearest
    )

    print("Minimum:", image.min())
    print("Maximum:", image.max())
    print("Valid pixels:", image.count())
    print("Masked pixels:", image.mask.sum() if hasattr(image.mask, "sum") else 0)

plt.figure(figsize=(10, 10))
plt.imshow(image, cmap="gray", origin="upper")
plt.title("MARSCOPE — Aligned Jezero CTX Orthomosaic")
plt.xlabel("Image columns")
plt.ylabel("Image rows")
plt.colorbar(label="Image intensity")
plt.tight_layout()
plt.savefig("data/processed/ctx_preview.png", dpi=150)
plt.show()

print("Preview saved: data/processed/ctx_preview.png")
