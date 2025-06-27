# ========== YENİ/GÜNCELLENMİŞ DOSYA: api/setup.py ==========
from setuptools import setup, find_packages

setup(
    # Bu satır, setuptools'a paketlerin 'src' klasörünün içinde
    # olduğunu söyler.
    package_dir={"": "src"},
    
    # Bu satır, 'src' klasörünün içindeki tüm Python paketlerini
    # (azuraforge_api ve altındakiler) otomatik olarak bulur.
    packages=find_packages(where="src"),
)