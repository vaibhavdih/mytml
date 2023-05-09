import os
import magic as magik
from zipfile import ZipFile

MAX_SIZE = 10 * 1024 * 1024
MIN_SIZE = 10


class Validator:
    def __init__(self, file):
        self.file = file

    def validate(self):
        print("validating === ")
        self._validate_size()
        self._validate_content_type()
        self._validate_zip_content()

    def _validate_size(self):
        size = os.path.getsize(self.file.name)
        if size > MAX_SIZE or size < MIN_SIZE:
            raise Exception("File Size Validation Error")

    def _get_mime_type(self):
        magic = magik.Magic(mime=True)
        return magic.from_file(self.file.name)

    def _validate_content_type(self):
        mime = self._get_mime_type()
        if mime not in [
            "application/vnd.ms-visio.drawing.main+xml",
            "application/octet-stream",
        ]:
            raise Exception("File Content Type Validation Error")

    def _validate_zip_content(self):
        mime = self._get_mime_type()
        if mime == "application/zip":
            with ZipFile(self.file.name) as myzip:
                if not any(
                    "[Content_Types].xml" == _file.filename for _file in myzip.filelist
                ):
                    raise Exception("File Zip format validation failed")


if __name__ == "__main__":
    # a = Validator(
    #     file=open("/home/vaibhav/Documents/Tools/my/data/visio-basic-example.vsdx")
    # )
    # print(a.validate())

    x = file = open("/home/vaibhav/Documents/Tools/my/data/visio-basic-example.vsdx")
