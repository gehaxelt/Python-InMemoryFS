#!/usr/bin/env python

from __future__ import with_statement

import os
import sys
import errno
import copy
import io
import time

from fuse import FUSE, FuseOSError, Operations

"""
http://man7.org/linux/man-pages/man7/inode.7.html
           S_IFSOCK   0140000   socket
           S_IFLNK    0120000   symbolic link
           S_IFREG    0100000   regular file
           S_IFBLK    0060000   block device
           S_IFDIR    0040000   directory
           S_IFCHR    0020000   character device
           S_IFIFO    0010000   FIFO
"""

class InMemoryFS(Operations):
    def __init__(self):
        self.fs = {
            "/": {}
        }
        self.meta = {
            "/": {
                'st_atime': time.time(),
                'st_mtime': time.time(),
                'st_ctime': time.time(),
                'st_mode': 0o00040777,
                'st_nlink': 0,
                'st_size': 0,
                'st_gid': os.getuid(),
                'st_uid': os.getgid(),
                }
        }

    # Helpers
    # =======

    def _full_path(self, partial):
        if partial.startswith("/"):
            partial = partial[1:]
        path = os.path.join("/", partial)
        return path

    def _the_dir(self, f_path):
        d = "/".join(f_path.split("/")[:-1])
        return '/' if d == '' else d

    def _the_file(self, f_path):
        return f_path.split("/")[-1]

    def _debug():
        print(self.fs)
        print(self.meta)

    # Filesystem methods
    # ==================

    def access(self, path, mode):
        pass

    def chmod(self, path, mode):
        print("[*] chmod: ", path)
        raise FuseOSError(38)

    def chown(self, path, uid, gid):
        print("[*] chown: ", path)
        raise FuseOSError(38)

    def getattr(self, path, fh=None):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)
        print("[*] getattr: ", full_path)

        if not full_path in self.meta.keys():
            raise FuseOSError(errno.ENOENT)

        if the_dir in self.fs and the_file in self.fs[the_dir]:
            self.meta[full_path]['st_size'] = len(self.fs[the_dir][the_file])
        return self.meta[full_path]

    def readdir(self, path, fh):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)

        print("[*] readdir: ", full_path, the_dir)

        dirents = ['.', '..']
        if the_dir in self.fs.keys():
            dirents.extend([f for f in self.fs[full_path]])

        dirents.extend(list(map(lambda y: y.lstrip(full_path), filter(lambda x: x.startswith(the_dir) and "/" not in x.lstrip(full_path) and x.lstrip(full_path) != '', self.fs.keys()))))
        print(dirents)
        for r in dirents:
            yield r

    def readlink(self, path):
        print("[*] readlink")
        raise FuseOSError(38)

    def mknod(self, path, mode, dev):
        print("[*] mknod")
        pass

    def rmdir(self, path):
        full_path = self._full_path(path)

        print("[*] rmdir: ", full_path)
        if full_path in self.fs.keys():
            del self.fs[full_path]
            del self.meta[full_path]

    def mkdir(self, path, mode):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] mkdir: ", full_path, the_dir, the_file)

        if not the_dir in self.fs.keys():
            raise FuseOSError(errno.ENOENT)

        if the_file in self.fs[the_dir].keys():
            raise FuseOSError(errno.EEXIST)

        self.fs[full_path] = {}
        self.meta[full_path] =  {
                'st_atime': time.time(),
                'st_mtime': time.time(),
                'st_ctime': time.time(),
                'st_mode': 0o0040777,
                'st_nlink': 0,
                'st_size': 0,
                'st_gid': os.getuid(),
                'st_uid': os.getgid(),
                }

    def statfs(self, path):
        print("[*] statfs")
        # full_path = self._full_path(path)
        # stv = os.statvfs(full_path)
        # return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
        #     'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
        #     'f_frsize', 'f_namemax'))
        raise FuseOSError(38)

    def unlink(self, path):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] unlink: ", full_path, the_dir, the_file)

        if not the_dir in self.fs.keys():
            raise FuseOSError(38)

        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        del self.fs[the_dir][the_file]
        del self.meta[full_path]

        return 0


    def symlink(self, name, target):
        print("[*] symlink")
        raise FuseOSError(38)

    def rename(self, old, new):
        full_path_old = self._full_path(old)
        the_dir_old = self._the_dir(full_path_old)
        the_file_old = self._the_file(full_path_old)

        full_path_new = self._full_path(new)
        the_dir_new = self._the_dir(full_path_new)
        the_file_new = self._the_file(full_path_new)


        print("[*] rename: ", full_path_old, the_dir_old, the_file_old)
        print("[*] rename: ", full_path_new, the_dir_new, the_file_new)

        if not the_dir_old in self.fs.keys():
            raise FuseOSError(errno.ENOENT)

        if not the_dir_new in self.fs.keys():
            raise FuseOSError(errno.ENOENT)

        if not the_file_old in self.fs[the_dir_old].keys():
            raise FuseOSError(errno.ENOENT)

        if the_file_new in self.fs[the_dir_new].keys():
            raise FuseOSError(errno.EEXIST)

        self.fs[the_dir_new][the_file_new] = copy.deepcopy(self.fs[the_dir_old][the_file_old])
        del self.fs[the_dir_old][the_file_old]
        del self.fs[the_dir_old]

        self.meta[full_path_new] = copy.deepcopy(self.meta[full_path_old])
        del self.meta[full_path_old]


    def link(self, target, name):
        print("[*] link")
        raise FuseOSError(38)

    def utimens(self, path, times=None):
        full_path = self._full_path(path)

        print("[*] utimens: ", full_path)
        if not full_path in self.meta.keys():
            raise FuseOSError(errno.ENOENT)

        if times:
            self.meta[full_path]['st_atime'] = times[0]
            self.meta[full_path]['st_mtime'] = times[1]
        else:
            self.meta[full_path]['st_atime'] = time.time()
            self.meta[full_path]['st_mtime'] = time.time()

        return 0

    # File methods
    # ============

    def open(self, path, flags):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] open: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)
        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        return 1337

    def create(self, path, mode, fi=None):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] create: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)

        if the_file in self.fs[the_dir].keys():
            raise FuseOSError(errno.EEXIST)

        self.fs[the_dir][the_file] = []
        self.meta[full_path] = {
                'st_atime': time.time(),
                'st_mtime': time.time(),
                'st_ctime': time.time(),
                'st_mode': 0o0100777,
                'st_nlink': 0,
                'st_size': 0,
                'st_gid': os.getuid(),
                'st_uid': os.getgid(),
                }
        return 1337 # we don't use file handles, so any random number should suffice, I guess?


    def read(self, path, length, offset, fh):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] read: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)

        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        return bytes(self.fs[the_dir][the_file][offset:length])


    def write(self, path, buf, offset, fh):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] write: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)
        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        self.fs[the_dir][the_file][offset:] += bytes(buf)
        return len(buf)

    def truncate(self, path, length, fh=None):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] truncate: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)
        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        self.fs[the_dir][the_file] = []

    def flush(self, path, fh):
        print("[*] flush")
        raise FuseOSError(38)

    def release(self, path, fh):
        full_path = self._full_path(path)
        the_dir = self._the_dir(full_path)
        the_file = self._the_file(full_path)

        print("[*] release: ", full_path, the_dir, the_file)
        if not the_dir in self.fs.keys():
            raise FuseOSError(38)
        if not the_file in self.fs[the_dir].keys():
            raise FuseOSError(38)

        pass

    def fsync(self, path, fdatasync, fh):
        print("[*] fsync")
        raise FuseOSError(38)


def main(mountpoint):
    FUSE(InMemoryFS(), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
    main(sys.argv[1])