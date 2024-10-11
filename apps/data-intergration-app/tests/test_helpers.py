from app.helpers import get_csv_reader


def test_get_csv_reader_comma_separated():
    csv_data = ['foo,bar,baz', 'foo,test,test']
    reader = get_csv_reader(csv_data)
    for row in reader:
        assert row['foo'] == 'foo'


def test_get_csv_reader_tab_separated():
    csv_data = ['foo\tbar\tbaz', 'foo\ttest\ttest']
    reader = get_csv_reader(csv_data)
    for row in reader:
        assert row['foo'] == 'foo'
