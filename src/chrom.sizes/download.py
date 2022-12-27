import os
import sys
import requests


# T2T?
allowed_genome = [
    "hg19", "hg38",
    "panTro4", "panTro5", "panTro6",
    "gorGor3", "gorGor4",

    "nomLeu3",
    "papAnu2",
    "rheMac2", "rheMac3", "rheMac8", "rheMac10",

    "calJac3", "calJac4",
    "bosTau8",
    "oviAri4",

    "susScr3", "susScr11",
    "oryCun2",
    "canFam2", "canFam3",

    "mm9", "mm10", "mm39",
    "rn4", "rn6", "rn7",
    "monDom5",

    "GRCg7w", "GRCg7b", "galGal5", "galGal6",
    "xenTro10",
    "danRer7", "danRer10", "danRer11",

    "lepOcu1",
    "dm6",
    "ce11",

    "araTha1",
    "b_chilifu_v3",
    "aplCal3",

    "",
    "",
    "",

    "sacCer3",
    "Pfal3D7",
    "",

    "", "", "", "", "",
    "", "",

]


for assembly in allowed_genome:
    html = f'<option value="{assembly}">{assembly}</option>'
    print(html)


for assembly in allowed_genome:
    url = f"http://hgdownload.soe.ucsc.edu/goldenPath/{assembly}/bigZips/{assembly}.chrom.sizes"
    # print(url)

    response = requests.get(url)
    if response.status_code != 200:
        print(assembly)
        continue

    f = open("%s.chrom.sizes" % assembly, "w")
    f.write(response.text)
    f.close()
