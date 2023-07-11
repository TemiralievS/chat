from setuptools import setup, find_packages

setup(name="message_chat_server",
      version="0.0.1",
      description="message_chat_server",
      author="Temiraliev Sergey",
      author_email="okillington12@gmail.com",
      packages=find_packages(),
      install_requires=['PyQt5', 'sqlalchemy', 'pycryptodome', 'pycryptodomex']
      )