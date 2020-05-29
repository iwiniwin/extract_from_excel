#!/usr/bin/python
# ----------------------------------------------------------------------------
# cocos-console: command line tool manager for cocos2d-x
#
# Author: Ricardo Quesada
# Copyright 2013 (C) Zynga, Inc
#
# License: MIT
# ----------------------------------------------------------------------------
'''
Command line tool manager
'''

# -*- coding:utf-8 -*-
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import sys
import os
import shutil
import string
import subprocess
import errno
import re
from xml.etree import ElementTree as ET
import zipfile
import time
from stat import *
import hashlib

class table(object): pass

global nextLineIsAppid;
nextLineIsAppid = False;

# 设置文件中key对应的值
# 例如_gameVersion=2 
# setValue(filepath, "_gameVersion", 3)调用后，_gameVersion=3
# 注意key和value中有正则特殊字符时需要转换
def setValue(filepath, key, value):
    pattern = re.compile(key + "\s*=")
    pattern2 = re.compile("(?<==).*")
    # return pattern.sub('', string)
    if key is None or value is None:
        raise TypeError
    f1 = open(filepath, "rb")
    content = ""
    for line in f1:
        strline = line.decode('utf8')
        match = pattern.search(strline)
        match2 = pattern2.search(strline)
        if match and match2:
            content += strline.replace(match2.group(0), " " + value)
        else:
            content += strline
    f1.close()
    f2 = open(filepath, "wb")
    f2.write(content.encode('utf8'))
    f2.close()
    pass

#替换字符串
def replace_string(filepath, src_string, dst_string):
    """ From file's content replace specified string
    Arg:
        filepath: Specify a file contains the path
        src_string: old string
        dst_string: new string
    """
    if src_string is None or dst_string is None:
        raise TypeError

    content = ""
    f1 = open(filepath, "rb")
    for line in f1:
        strline = line.decode('utf8')
        if src_string in strline:
            content += strline.replace(src_string, dst_string)
        else:
            content += strline
    f1.close()
    f2 = open(filepath, "wb")
    f2.write(content.encode('utf8'))
    f2.close()

#能把文件中 sstr的字符串，全替换成rstr
#示例modifyip(rem.txt,"a","A")
#能将rem.txt文件中的所有小写a字符串替换成大写A
def modifyip(tfile,sstr,rstr):
    try:
        lines=open(tfile,'r').readlines()
        flen=len(lines)-1
        for i in range(flen):
            if sstr in lines[i]:
                lines[i]=lines[i].replace(sstr,rstr)
        open(tfile,'w').writelines(lines)
        
    except Exception,e:
        print e

def add_path_prefix(path_str):
    if path_str.startswith("\\\\?\\"):
        return path_str

    ret = "\\\\?\\" + os.path.abspath(path_str)
    ret = ret.replace("/", "\\")
    return ret

def copy_files_in_dir(src, dst):
    for item in os.listdir(src):
        path = os.path.join(src, item)
        if os.path.isfile(path):
            path = add_path_prefix(path)
            copy_dst = add_path_prefix(dst)
            print("copy " + path + " to " + copy_dst)
            shutil.copy(path, copy_dst)
        if os.path.isdir(path):
            new_dst = os.path.join(dst, item)
            if not os.path.isdir(new_dst):
                os.makedirs(add_path_prefix(new_dst))
            copy_files_in_dir(path, new_dst)


def copy_files_with_config(config, src_root, dst_root):
    src_dir = config["from"]
    dst_dir = config["to"]

    src_dir = os.path.join(src_root, src_dir)
    dst_dir = os.path.join(dst_root, dst_dir)

    include_rules = None
    if "include" in config:
        include_rules = config["include"]
        include_rules = convert_rules(include_rules)

    exclude_rules = None
    if "exclude" in config:
        exclude_rules = config["exclude"]
        exclude_rules = convert_rules(exclude_rules)

    copy_files_with_rules(
        src_dir, src_dir, dst_dir, include_rules, exclude_rules)


def copy_files_with_rules(src_rootDir, src, dst, include=None, exclude=None):
    if os.path.isfile(src):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))

        copy_src = add_path_prefix(src)
        copy_dst = add_path_prefix(dst)
        shutil.copy(copy_src, copy_dst)
        return

    if (include is None) and (exclude is None):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))
        copy_files_in_dir(src, dst)
    elif (include is not None):
        # have include
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            rel_path = os.path.relpath(abs_path, src_rootDir)
            if os.path.isdir(abs_path):
                sub_dst = os.path.join(dst, name)
                copy_files_with_rules(
                    src_rootDir, abs_path, sub_dst, include=include)
            elif os.path.isfile(abs_path):
                if _in_rules(rel_path, include):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)
    elif (exclude is not None):
        # have exclude
        # print(exclude[1])
        # print(src)
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            # print(abs_path)
            rel_path = os.path.relpath(abs_path, src_rootDir)

            if os.path.isdir(abs_path):
                sub_dst = os.path.join(dst, name)


                if not os.path.exists(sub_dst):
                        os.makedirs(add_path_prefix(sub_dst))

                copy_files_with_rules(
                    src_rootDir, abs_path, sub_dst, exclude=exclude)

            elif os.path.isfile(abs_path):
                if not _in_rules(rel_path, exclude):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)

def copy_files_with_rules2(src_rootDir, src, dst, include=None, exclude=None):
    if os.path.isfile(src):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))

        copy_src = add_path_prefix(src)
        copy_dst = add_path_prefix(dst)
        shutil.copy(copy_src, copy_dst)
        print("copy " + copy_src +" to " + copy_dst)
        return

    if (include is None) and (exclude is None):
        if not os.path.exists(dst):
            os.makedirs(add_path_prefix(dst))
        copy_files_in_dir(src, dst)
    elif (include is not None):
        # have include
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            rel_path = os.path.relpath(abs_path, src_rootDir)
            if os.path.isdir(abs_path):
                sub_dst = os.path.join(dst, name)
                copy_files_with_rules(
                    src_rootDir, abs_path, sub_dst, include=include)
            elif os.path.isfile(abs_path):
                if _in_rules(rel_path, include):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)
    elif (exclude is not None):
        # have exclude
        # print(exclude[1])
        for name in os.listdir(src):
            abs_path = os.path.join(src, name)
            # print(abs_path)
            rel_path = os.path.relpath(abs_path, src_rootDir)
            # print("rel_path " + rel_path)
            if os.path.isdir(abs_path):
                if not _in_rules2(name,exclude):
                    sub_dst = os.path.join(dst, name)
                    if not os.path.exists(sub_dst):
                        os.makedirs(add_path_prefix(sub_dst))
                    copy_files_with_rules2(
                        src_rootDir, abs_path, sub_dst, exclude=exclude)

            elif os.path.isfile(abs_path):
                if not _in_rules(rel_path, exclude):
                    if not os.path.exists(dst):
                        os.makedirs(add_path_prefix(dst))

                    abs_path = add_path_prefix(abs_path)
                    copy_dst = add_path_prefix(dst)
                    shutil.copy(abs_path, copy_dst)
                    print("copy " + abs_path +" to " + copy_dst)

def _in_rules(rel_path, rules):
    import re
    ret = False
    path_str = rel_path.replace("\\", "/")
    for rule in rules:
        if re.match(rule, path_str):
        # if rule in path_str:
            ret = True

    return ret

def _in_rules2(name, rules):
    import re
    ret = False
    for rule in rules:
        if name in rule:
            ret = True

    return ret


def convert_rules(rules):
    ret_rules = []
    for rule in rules:
        ret = rule.replace('.', '\\.')
        ret = ret.replace('*', '.*')
        ret = "%s" % ret
        ret_rules.append(ret)

    return ret_rules

def _makedirs(name, mode=0777):
    """makedirs(path [, mode=0777])

    Super-mkdir; create a leaf directory and all intermediate ones.
    Works like mkdir, except that any intermediate path segment (not
    just the rightmost) will be created if it does not exist.  This is
    recursive.

    """
    head, tail = os.path.split(name)
    if not tail:
        head, tail = path.split(head)
    if head and tail and not os.path.exists(head):
        try:
            makedirs(head, mode)
        except OSError, e:
            # be happy if someone already created the path
            if e.errno != errno.EEXIST:
                raise
        if tail == curdir:           # xxx/newdir/. exists if xxx/newdir exists
            return
    if os.path.exists(name):
	return
    mkdir(name, mode)
    
class _Error(EnvironmentError):
    pass

def copytreeForOver(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    The destination directory must not already exist.
    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()
    _makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
	if symlinks and os.path.islink(srcname):
	    linkto = os.readlink(srcname)
	    os.symlink(linkto, dstname)
	elif os.path.isdir(srcname):
	    if not os.path.exists(dstname):
		continue		
	    copytreeForOver(srcname, dstname, symlinks, ignore)
	elif os.path.exists(dstname):
	    shutil.copy2(srcname, dstname)
    shutil.copystat(src, dst)

def ElementIsDefined(xmlFile,element):
    try:
	xmlObj = ET.parse(xmlFile)
	if xmlObj == None:
	    return False
	elementTag = xmlObj.find("voiceAppId")
	return elementTag != None
    except:
	return False

#去除字符串中的所有空白字符
def strip(string):
    pattern = re.compile("\s")
    return pattern.sub('', string)

# 拷贝文件或文件夹
def copyf(src, dst):
    if os.path.isfile(src):
        removef(dst)
        shutil.copyfile(src, dst)
    elif os.path.isdir(src):
        removef(dst)
        shutil.copytree(src, dst)

# 删除文件或文件夹
def removef(src):
    if os.path.exists(src):
        if os.path.isdir(src):
            try:
                shutil.rmtree(src)
            except Exception as e:
                removef(src)
        elif os.path.isfile(src):
            os.remove(src)    

# 打zip包
def zipDir(dir):
    azip = zipfile.ZipFile(dir + ".zip", 'w')
    TimeForChange = '2018-04-16 15:19:21'
    ConverTime = time.mktime(time.strptime(TimeForChange,'%Y-%m-%d %H:%M:%S') )
    for current, subfolder, files in os.walk(dir):

        fpath = current.replace(dir, "")
        fpath = fpath and fpath + os.sep or ''
        for file in files:
            os.utime(os.path.join(current, file), (ConverTime, ConverTime))
            azip.write(os.path.join(current, file), fpath + file)
    azip.close()

        
# 检测打包
def pack(src, filter = []):
    if not os.path.isdir(src):
        return
    for item in os.listdir(src):
        path = os.path.join(src, item)
        if os.path.isfile(path): 
            if os.path.basename(path) == "init.lua":
                # 打包
                zipDir(src)
                removef(src)
                return
    for item in os.listdir(src):
        if item in filter:
            continue
        path = os.path.join(src, item)
        if os.path.isdir(path):
            pack(path, filter)

def getFileMD5(filepath):  
        if os.path.isfile(filepath):  
            f = open(filepath,'rb')  
            md5obj = hashlib.md5()  
            md5obj.update(f.read())  
            hash = md5obj.hexdigest()  
            f.close()  
            return str(hash).upper()  
        return None  


# zipDir("E:\\Boyaa\\BoyaaIDE\\BoyaaIDE_dev\\Publish\\a")
# zipDir("E:\\Boyaa\\BoyaaIDE\\BoyaaIDE_dev\\Publish\\b")

# print(getFileMD5("E:\\Boyaa\\BoyaaIDE\\BoyaaIDE_dev\\Publish\\a.zip"))
# print(getFileMD5("E:\\Boyaa\\BoyaaIDE\\BoyaaIDE_dev\\Publish\\b.zip"))
