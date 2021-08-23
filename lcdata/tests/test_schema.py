from astropy.table import Table, MaskedColumn
import numpy as np
import pytest

import lcdata


@pytest.fixture
def schema():
    def default_function():
        default_function.count += 1
        return default_function.count

    default_function.count = 0

    return {
        'a': {
            'dtype': np.float64,
            'required': True,
            'aliases': ('a', 'aa'),
        },
        'b': {
            'dtype': bytes,
            'default': 'test',
            'aliases': ('b', 'bb'),
        },
        'c': {
            'dtype': np.int32,
            'default_function': default_function,
            'aliases': ('c', 'cc'),
        },
    }


@pytest.fixture
def table():
    return Table({
        'a': np.array([0., 1., 2.], dtype=np.float64),
        'b': np.array(['x', 'y', 'z'], dtype=bytes),
        'c': np.array([10, 20, 30], dtype=np.int32),
    })


def test_get_default_value(schema):
    val = lcdata.schema.get_default_value(schema, 'b')
    assert val == 'test'


def test_get_default_value_required(schema):
    with pytest.raises(ValueError):
        lcdata.schema.get_default_value(schema, 'a')


def test_get_default_value_function(schema):
    val1 = lcdata.schema.get_default_value(schema, 'c')
    val2 = lcdata.schema.get_default_value(schema, 'c')
    assert val1 == 1 and val2 == 2


def test_get_default_value_function_multiple(schema):
    val = lcdata.schema.get_default_value(schema, 'c', count=5)
    assert len(val) == 5


def test_find_alias(schema):
    names = ['aa', 'bb', 'cc']
    assert lcdata.schema.find_alias(names, schema['a']['aliases']) == 'aa'


def test_find_alias_same(schema):
    names = ['a', 'b', 'c']
    assert lcdata.schema.find_alias(names, schema['b']['aliases']) == 'b'


def test_find_alias_capitalization(schema):
    names = ['Aa', 'Bb', 'Cc']
    assert lcdata.schema.find_alias(names, schema['c']['aliases']) == 'Cc'


def test_find_alias_spaces(schema):
    names = ['A_ a_', 'B_ b_', 'C_ c_']
    assert lcdata.schema.find_alias(names, schema['b']['aliases']) == 'B_ b_'


def test_find_alias_fail(schema):
    names = ['a', 'c']
    assert lcdata.schema.find_alias(names, schema['b']['aliases']) is None


def test_format_table(table, schema):
    format_table = lcdata.schema.format_table(table, schema, verbose=True)
    assert table is format_table


def assert_same_table(table_1, table_2):
    # Helper to assert that two tables are the same.
    assert table_1.colnames == table_2.colnames
    for column_1, column_2 in zip(table_1.itercols(), table_2.itercols()):
        assert all(column_1 == column_2)


def test_format_table_alias(table, schema):
    input_table = table.copy()
    input_table.rename_column('b', 'bb')
    format_table = lcdata.schema.format_table(input_table, schema, verbose=True)
    assert_same_table(table, format_table)


def test_format_table_reorder(table, schema):
    input_table = table[['b', 'a', 'c']]
    format_table = lcdata.schema.format_table(input_table, schema, verbose=True)
    assert_same_table(table, format_table)


def test_format_table_default(table, schema):
    del table['b']
    format_table = lcdata.schema.format_table(table, schema, verbose=True)
    assert format_table['b'][0] == 'test'


def test_format_table_dtype(table, schema):
    table['a'] = table['a'].astype(int)
    format_table = lcdata.schema.format_table(table, schema, verbose=True)
    assert format_table['a'].dtype.type is np.float64


def test_format_table_masked(table, schema):
    table['b'] = MaskedColumn(['hi', 'hi', 'hi'], mask=[True, False, False])
    format_table = lcdata.schema.format_table(table, schema, verbose=True)
    assert format_table['b'][0] == 'test'


def test_format_table_masked_function(table, schema):
    table['c'] = MaskedColumn([0, 0, 0], mask=[True, True, False])
    format_table = lcdata.schema.format_table(table, schema, verbose=True)
    assert all(format_table['c'] == [1, 2, 0])