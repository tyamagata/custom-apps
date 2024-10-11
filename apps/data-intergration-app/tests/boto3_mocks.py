from datetime import datetime
from pytz import UTC


class BotoObject:
    def __init__(self):
        self.key = "tc-rover-s3-test/rover example s2s.csv"
        self.last_modified = UTC.localize(datetime.utcnow())
        self.ContentType = ""

    def get(self):
        if len(self.ContentType) == 0:
            return {"ContentType": "not_a_directory"}
        else:
            return {"ContentType": "application/x-directory"}

    def set_content_type(self, content_type):
        self.ContentType = content_type


class BotoObjects:
    def __init__(self):
        pass

    def filter(self, Prefix):
        return [BotoObject()]


class BotoBucketMock:
    def __init__(self):
        self.objects = BotoObjects()


class BotoResourceMock:
    def __init__(self, protocol, aws_access_key_id, aws_secret_access_key):
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key

    def Bucket(self, bucket_name):
        return BotoBucketMock()
