import pathlib

import pytest

import trio
from trio._file_io._path import AsyncAutoWrapperType as Type


@pytest.fixture
def path(tmpdir):
    p = str(tmpdir.join('test'))
    return trio.AsyncPath(p)


def method_pair(path, method_name):
    path = pathlib.Path(path)
    async_path = trio.AsyncPath(path)
    return getattr(path, method_name), getattr(async_path, method_name)


async def test_open_is_async_context_manager(path):
    async with await path.open('w') as f:
        assert isinstance(f, trio.AsyncIOWrapper)

    assert f.closed


async def test_forward_magic(path):
    assert str(path) == str(path._wrapped)


async def test_forwarded_properties(path):
    # use `name` as a representative of forwarded properties

    assert 'name' in dir(path)
    assert path.name == 'test'


async def test_async_method_signature(path):
    # use `resolve` as a representative of wrapped methods

    assert path.resolve.__name__ == 'resolve'
    assert path.resolve.__qualname__ == 'AsyncPath.resolve'

    assert 'pathlib.Path.resolve' in path.resolve.__doc__


@pytest.mark.parametrize('method_name', ['is_dir', 'is_file'])
async def test_compare_async_stat_methods(method_name):

    method, async_method = method_pair('.', method_name)

    result = method()
    async_result = await async_method()

    assert result == async_result


async def test_invalid_name_not_wrapped(path):
    with pytest.raises(AttributeError):
        getattr(path, 'invalid_fake_attr')


@pytest.mark.parametrize('method_name', ['absolute', 'resolve'])
async def test_async_methods_rewrap(method_name):

    method, async_method = method_pair('.', method_name)

    result = method()
    async_result = await async_method()

    assert isinstance(async_result, trio.AsyncPath)
    assert str(result) == str(async_result)


async def test_forward_methods_rewrap(path, tmpdir):
    with_name = path.with_name('foo')
    with_suffix = path.with_suffix('.py')

    assert isinstance(with_name, trio.AsyncPath)
    assert with_name == tmpdir.join('foo')
    assert isinstance(with_suffix, trio.AsyncPath)
    assert with_suffix == tmpdir.join('test.py')


async def test_repr():
    path = trio.AsyncPath('.')

    assert repr(path) == 'AsyncPath(.)'


class MockWrapped:
    unsupported = 'unsupported'
    _private = 'private'


class MockWrapper:
    _forwards = MockWrapped
    _wraps = MockWrapped


async def test_type_forwards_unsupported():
    with pytest.raises(TypeError):
        Type.generate_forwards(MockWrapper, {})


async def test_type_wraps_unsupported():
    with pytest.raises(TypeError):
        Type.generate_wraps(MockWrapper, {})


async def test_type_forwards_private():
    Type.generate_forwards(MockWrapper, {'unsupported': None})

    assert not hasattr(MockWrapper, '_private')


async def test_type_wraps_private():
    Type.generate_wraps(MockWrapper, {'unsupported': None})

    assert not hasattr(MockWrapper, '_private')
