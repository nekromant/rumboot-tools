from rumboot.scripting import engine

connection = engine("oi10")

engine.run("file.bin")
data = engine.read32(0x100)
engine.write32(0x100, data)
engine.upload(0x10000, "file.bin")
engine.download("file.bin", 0x10000)
