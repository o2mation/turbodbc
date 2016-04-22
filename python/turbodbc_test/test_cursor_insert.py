import datetime

from cursor_test_case import open_cursor
from query_fixture import query_fixture
from for_each_database import for_each_database


def generate_microseconds_with_precision(digits):
    microseconds = 0;
    for i in xrange(digits):
        microseconds = 10 * microseconds + i + 1
    for i in xrange(6 - digits):
        microseconds *= 10

    return microseconds


def _test_insert_many(configuration, fixture_name, data):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, fixture_name) as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?)".format(table_name), data)
            assert len(data) == cursor.rowcount
            cursor.execute("SELECT a FROM {} ORDER BY a".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert data == inserted


@for_each_database
def test_insert_with_execute(dsn, configuration):
    to_insert = [1]

    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.execute("INSERT INTO {} VALUES (?)".format(table_name), to_insert)
            assert 1 == cursor.rowcount
            cursor.execute("SELECT a FROM {}".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert [to_insert] == inserted


@for_each_database
def test_insert_string_column(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT STRING',
                      [['hello'], ['my'], ['test case']])


@for_each_database
def test_insert_bool_column(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT BOOL',
                      [[False], [True], [True]])


@for_each_database
def test_insert_integer_column(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT INTEGER',
                      [[1], [2], [3]])


@for_each_database
def test_insert_double_column(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT DOUBLE',
                      [[1.23], [2.71], [3.14]])


@for_each_database
def test_insert_date_column(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT DATE',
                      [[datetime.date(2015, 12, 31)],
                       [datetime.date(2016, 1, 15)],
                       [datetime.date(2016, 2, 3)]])

@for_each_database
def test_insert_timestamp_column(dsn, configuration):
    supported_digits = configuration['capabilities']['fractional_second_digits']
    fractional = generate_microseconds_with_precision(supported_digits)

    _test_insert_many(configuration,
                      'INSERT TIMESTAMP',
                      [[datetime.datetime(2015, 12, 31, 1, 2, 3, fractional)],
                       [datetime.datetime(2016, 1, 15, 4, 5, 6, fractional * 2)],
                       [datetime.datetime(2016, 2, 3, 7, 8, 9, fractional * 3)]])


@for_each_database
def test_insert_null(dsn, configuration):
    _test_insert_many(configuration,
                      'INSERT INTEGER',
                      [[None]])

@for_each_database
def test_insert_mixed_data_columns(dsn, configuration):
    # second column has mixed data types in the same column
    # first column makes sure values of "good" columns are not affected
    to_insert = [[23, 1.23],
                 [42, 2]]

    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT MIXED') as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?, ?)".format(table_name), to_insert)
            assert len(to_insert) == cursor.rowcount
            cursor.execute("SELECT a, b FROM {} ORDER BY a".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert to_insert == inserted


@for_each_database
def test_insert_no_parameter_list(dsn, configuration):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?)".format(table_name))
            assert 0 == cursor.rowcount
            cursor.execute("SELECT a FROM {}".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert 0 == len(inserted)


@for_each_database
def test_insert_empty_parameter_list(dsn, configuration):
    to_insert = []

    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?)".format(table_name), to_insert)
            assert 0 == cursor.rowcount
            cursor.execute("SELECT a FROM {}".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert to_insert == inserted


@for_each_database
def test_insert_number_of_rows_exceeds_buffer_size(dsn, configuration):
    buffer_size = 100
    numbers = buffer_size * 2 + 17
    data = [[i] for i in xrange(numbers)]
    
    with open_cursor(configuration, parameter_sets_to_buffer=buffer_size) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?)".format(table_name), data)
            assert len(data) == cursor.rowcount
            cursor.execute("SELECT a FROM {} ORDER BY a".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert data == inserted


@for_each_database
def test_description_after_insert(dsn, configuration):
    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT INTEGER') as table_name:
            cursor.execute("INSERT INTO {} VALUES (42)".format(table_name))
            assert None == cursor.description


@for_each_database
def test_string_with_differing_lengths(dsn, configuration):
    long_strings = [['x' * 5], ['x' * 50], ['x' * 500]]
    to_insert = [[1]] # use integer to force rebind to string buffer afterwards
    to_insert.extend(long_strings)
    expected = [['1']]
    expected.extend(long_strings)

    with open_cursor(configuration) as cursor:
        with query_fixture(cursor, configuration, 'INSERT LONG STRING') as table_name:
            cursor.executemany("INSERT INTO {} VALUES (?)".format(table_name), to_insert)
            assert len(to_insert) == cursor.rowcount
            cursor.execute("SELECT a FROM {}".format(table_name))
            inserted = [list(row) for row in cursor.fetchall()]
            assert expected == inserted
