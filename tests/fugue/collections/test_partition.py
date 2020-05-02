import json

from fugue.collections.partition import PartitionSpec
from pytest import raises
from triad.collections.schema import Schema


def test_partition_spec():
    p = PartitionSpec()
    assert [] == p.partition_by
    "0" == p.num_partitions
    {} == p.presort
    "" == p.algo

    p = PartitionSpec(json.dumps(dict(partition_by=["a", "b", "c"], num_partitions=1)))
    assert ["a", "b", "c"] == p.partition_by
    assert "1" == p.num_partitions
    assert {} == p.presort
    assert "" == p.algo

    p = PartitionSpec(dict(partition_by=["a", "b", "c"], presort="d asc,e desc"))
    assert ["a", "b", "c"] == p.partition_by
    assert "0" == p.num_partitions
    assert dict(d=True, e=False) == p.presort
    assert "" == p.algo

    p = PartitionSpec(partition_by=["a", "b", "c"], presort="d,e desc", algo="EvEN")
    assert ["a", "b", "c"] == p.partition_by
    assert "0" == p.num_partitions
    assert dict(d=True, e=False) == p.presort
    assert "even" == p.algo

    # partition by overlaps with presort
    raises(SyntaxError, lambda: PartitionSpec(partition_by=[
           "a", "b", "c"], presort="a asc,e desc", algo="EvEN"))

    # partition by has dups
    raises(SyntaxError, lambda: PartitionSpec(partition_by=["a", "b", "b"]))

    # partition by has dups
    raises(SyntaxError, lambda: PartitionSpec(partition_by=["a", "b", "b"]))

    # bad input
    raises(TypeError, lambda: PartitionSpec(1))

    # bad presort
    raises(SyntaxError, lambda: PartitionSpec(presort="a xsc,e desc"))
    raises(SyntaxError, lambda: PartitionSpec(presort="a asc,a desc"))
    raises(SyntaxError, lambda: PartitionSpec(presort="a b asc,a desc"))

    p = PartitionSpec(dict(partition_by=["a"], presort="d asc,e desc"))
    assert dict(a=True, d=True, e=False) == p.get_sorts(
        Schema("a:int,b:int,d:int,e:int"))
    p = PartitionSpec(dict(partition_by=["e", "a"], presort="d asc"))
    assert p.get_key_schema(Schema("a:int,b:int,d:int,e:int")) == "e:int,a:int"


def test_partition_cursor():
    p = PartitionSpec(dict(partition_by=["b", "a"]))
    s = Schema("a:int,b:int,c:int,d:int")
    c = p.get_cursor(s, 2)
    assert c.row_schema == s
    assert c.key_schema == "b:int,a:int"

    c.set([1, 2, 2, 2], 5, 6)
    assert [2, 1] == c.key_value_array
    assert dict(a=1, b=2) == c.key_value_dict
    assert 2 == c["c"]
    assert [1, 2, 2, 2] == c.row
    assert 5 == c.partition_no
    assert 2 == c.physical_partition_no
    assert 6 == c.slice_no
