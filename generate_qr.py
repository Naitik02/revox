import qrcode

address = "TJ3kXn4XBnnQ2Wy932fmUFBGRHGXUKyo3U"
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)
qr.add_data(address)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")
img.save("deposit_qr.png")
print("QR Code generated successfully.")
