Python InMemoryFS with FUSE
============================

This is a simple toy implementation of an in-memory filesystem in python with FUSE (Filesystem In User SpacE).

DO NOT USE IN PRODUCTION!

Usage: 

```
python inmemfs.py <mountpoint>
```

Requirements:

```
pip install fusepy
```

BUGS/TODO:

- Files disappear when moving or being created in nested folders
- Permissions
- Better data structures

WORKS (tm):

- touch
- mkdir
- rmdir
- read/write files