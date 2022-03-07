#!/usr/bin/env python3
"""Tests for operations.nifti."""
from numpy import prod, asarray, zeros, unique
from numpy.random import rand

from pytest import raises

from crispyoctobroccoli.operations import nifti


# ### Unit tests
def test_vol_to_mat():
    a = rand(3, 4, 5, 6)
    b = nifti.vol_to_mat(a)
    c = b.reshape(a.shape, order='F')

    assert b.ndim == 2
    assert all(b.shape == ((prod(a.shape[:-1])), a.shape[-1]))
    assert all(a == c)

    a = rand(3, 4, 5)
    b = nifti.vol_to_mat(a)
    c = b.reshape(a.shape, order='F')

    assert b.ndim == 1
    assert b.shape == prod(a.shape)
    assert all(a == c)


def test_mat_to_vol():
    a = rand(3, 4, 5, 6)
    b = a.reshape((60, 6), order='F')
    c = nifti.mat_to_vol(b, asdata=a)

    assert c.ndim == 4
    assert c.shape == a.shape
    assert all(a == c)

    c = nifti.mat_to_vol(b, shape=a.shape)

    assert c.ndim == 4
    assert c.shape == a.shape
    assert all(a == c)

    c = nifti.mat_to_vol(b, shape=(6, 2, 5, 6), asdata=a)

    assert c.shape == a.shape


def test_apply_mask():
    m = asarray([0, 1, 0])
    a = rand(3, 3)

    b = nifti.apply_mask(a, m)
    assert (b == a[1, :])


def test_unmask():
    m = asarray([0, 1, 0])
    a = rand(3)
    b = zeros([3, 3])
    b[1, :] = a

    c = nifti.unmask(a, m, shape=b.shape)

    assert c.ndim == 2
    assert c.shape == b.shape
    assert all(c == b)

    c = nifti.unmask(a, m, asdata=b)

    assert c.ndim == 2
    assert c.shape == b.shape
    assert all(c == b)

    c = nifti.unmask(a, m, shape=(2, 2), asdata=b)

    assert c.shape == b.shape


def test_apply_atlas():
    m = asarray([0, 1, 1, 1, 1, 1])
    a = asarray([1, 2, 2, 3, 3, 0])
    d = rand(6, 10)
    c = zeros((3, 10))
    cm = zeros((2, 10))
    c[0, :] = d[0, :]
    c[1, :] = d[1:3, :].mean(axis=0)
    c[2, :] = d[4:6, :].mean(axis=0)
    cm[0, :] = d[1:3, :].mean(axis=0)
    cm[1, :] = d[4:6, :].mean(axis=0)

    r = nifti.apply_atlas(d, a)
    rm = nifti.apply_atlas(d, a, mask=m)

    assert r.ndim == 2
    assert r.shape == c.shape
    assert all(r == c)
    assert rm.shape == cm.shape
    assert all(rm == cm)


def test_unfold_atlas():
    m = asarray([0, 1, 1, 1, 1, 1])
    a = asarray([1, 2, 2, 3, 3, 0])
    c = rand((3, 10))
    cm = rand((2, 10))
    da = zeros((6, 10))
    dm = zeros((6, 10))
    label = unique(a)
    label = label[label > 0]
    for n, l in enumerate(label):
        da[a == l] = c[n, :]
    label = label[label > 1]
    for n, l in enumerate(label):
        dm[a == l] = cm[n, :]

    r = nifti.unfold_atlas(c, a)
    rm = nifti.unfold_atlas(cm, a, mask=m)

    assert r.ndim == 2
    assert r.shape == da.shape
    assert all(r == da)
    assert rm.shape == dm.shape
    assert all(rm == dm)


# ### Break tests
def break_mat_to_vol():
    with raises(ValueError) as errorinfo:
        nifti.mat_to_vol(rand(3))
    assert 'Both shape' in str(errorinfo.value)


def break_apply_mask():
    a = rand(3, 2, 5)
    m = rand(2, 2)
    with raises(ValueError) as errorinfo:
        nifti.apply_mask(a, m)
    assert f'shape {a.shape}' in str(errorinfo.value)
    assert f'shape {m.shape}' in str(errorinfo.value)


def break_unmask():
    a = rand(6, 5)
    m = rand(3)
    b = rand(2, 3, 5)

    with raises(ValueError) as errorinfo:
        nifti.unmask(a, m)
    assert 'shape and asdata' in str(errorinfo.value)

    with raises(ValueError) as errorinfo:
        nifti.unmask(a, m, shape=(2, 3))
    assert 'shape (2, 3)' in str(errorinfo.value)
    assert f'shape {m.shape}' in str(errorinfo.value)

    with raises(ValueError) as errorinfo:
        nifti.unmask(a, m, asdata=b)
    assert f'shape {b.shape}' in str(errorinfo.value)
    assert f'shape {m.shape}' in str(errorinfo.value)

    m = asarray([0, 0, 1, 0, 1, 1])
    with raises(ValueError) as errorinfo:
        nifti.unmask(a, m, shape=(3, 2, 5))
    assert f'dimension {a.shape[0]}' in str(errorinfo.value)
    assert f'{m.sum()} entries' in str(errorinfo.value)


def break_apply_atlas():
    d = rand(2, 3, 4, 5)
    a = rand(3, 2, 4)
    b = rand(2, 3, 4)
    m = rand(3, 2, 4)
    with raises(NotImplementedError) as errorinfo:
        nifti.apply_atlas(d, d)
    assert f'Files with {d.ndim}' in str(errorinfo.value)

    with raises(ValueError) as errorinfo:
        nifti.apply_atlas(d, b, m)
    assert f'shape {d.shape}' in str(errorinfo.value)
    assert f'mask with shape {m.shape}' in str(errorinfo.value)

    with raises(ValueError) as errorinfo:
        nifti.apply_atlas(d, a, b)
    assert f'atlas with shape {a.shape}' in str(errorinfo.value)
    assert f'shape {d.shape}' in str(errorinfo.value)


def break_unfold_atlas():
    d = rand(6, 5)
    a = rand(2, 3, 4)
    m = rand(3)
    with raises(ValueError) as errorinfo:
        nifti.apply_atlas(d, a, m)
    assert f'{m.shape}D mask on {a.shape}D atlas' in str(errorinfo.value)

    m = rand(3, 3)
    with raises(ValueError) as errorinfo:
        nifti.apply_atlas(d, a, m)
    assert f'atlas with shape {a.shape}' in str(errorinfo.value)
    assert f'mask with shape {m.shape}' in str(errorinfo.value)

    a = asarray([0, 1, 2])
    with raises(ValueError) as errorinfo:
        nifti.apply_atlas(d, a)
    assert f'data with shape {d.shape}' in str(errorinfo.value)
    assert '2 parcels' in str(errorinfo.value)