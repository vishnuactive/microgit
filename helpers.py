import os
import json
from datetime import datetime
import fnmatch
import zlib
import configparser
import hashlib
import chardet
import sys
import shelve
from collections import deque

GIT_DIR = ".microgit"

def repo_path(*path):
    return os.path.join(".microgit",*path)

def write_to_configfile(key=None,value=None,default=True):
    try:
        config = shelve.open(repo_path("config"))
        if default:
            config['init.defaultbranch'] = "master"
            config['user.name'] = "user"
            config["user.email"] = "a@a.com"
        else:
            config[key] = value
    except Exception as ex:
        raise ex
    
def read_from_config(key):
    try:
        config = shelve.open(repo_path("config"))
        return config[key]
    except Exception as ex:
        raise ex

def init():
    try:
        if os.path.exists(GIT_DIR):
            raise Exception("Git already initialized")
        else:
            os.mkdir(GIT_DIR)
            os.makedirs(repo_path("objects"))
            os.makedirs(repo_path("refs","heads"))
            write_to_configfile()
            with open(repo_path("HEAD"),"w") as file:
                main_branch = read_from_config("init.defaultbranch")
                file.write(f"ref: refs/heads/{main_branch}")
            print(f"Initialized Git Repository in the current directory at {os.path.join(os.getcwd(),'.microgit')}")
    except Exception as ex:
        raise ex
    
def hash_object(filename):
    try:
        sha1 = None
        content = None
        if not os.path.exists(filename):
            raise Exception(f"File not found : {filename}")
        with open(filename,"rb") as file:
            content = file.read()
        sha1 = hashlib.sha1(content).hexdigest()
        if not os.path.exists(repo_path("objects",sha1[:2])):
            os.makedirs(repo_path("objects",sha1[:2]))
        with open(repo_path("objects",sha1[:2],sha1[2:]),"wb") as file:
            file.write(zlib.compress(content))
        return sha1
    except Exception as ex:
        raise ex

def cat_file(commit_hash):
    try:
        commit_path = repo_path("objects",commit_hash[:2],commit_hash[2:])
        if not os.path.exists(commit_path):
            raise Exception(f"Commit id not found : {commit_hash}")
        content = None
        with open(commit_path,"rb") as file:
            content = zlib.decompress(file.read())
        return content.decode(chardet.detect(content)['encoding'])
    except Exception as ex:
        raise ex
    
def add(filenames):
    try:
        for filename in list(filter(lambda file:os.path.exists(file),file_list(filenames))):
            index_file_path = repo_path("index")
            if not os.path.exists(index_file_path):
                with open(index_file_path,"w") as file:
                    json.dump({},file)
            index_content = {}
            with open(index_file_path,"r") as file:
                index_content = json.load(file)
            commit_hashes = get_commit_hashes()
            if hash_object(filename) in commit_hashes:
                continue
            index_content[filename] = hash_object(filename)
            with open(index_file_path,"w") as file:
                json.dump(index_content,file,indent=4)
    except Exception as ex:
        raise ex
    
def commit(commit_message,parent2=None):
    try:
        index_file_path = repo_path("index")
        parent = get_head()
        if not os.path.exists(index_file_path):
            raise Exception("No index file")
        with open(index_file_path,"r") as file:
            index_file_content = json.load(file)
        if len(index_file_content) == 0:
            raise Exception(f"\nOn branch {get_branch_name()}\nNothing to commit. Working tree clean")
        user_name= read_from_config("user.name")
        user_email = read_from_config("user.email")
        commit_content = {"tree":index_file_content,"username":user_name,"email":user_email,"date":datetime.now().isoformat(),"message":commit_message}
        if parent:
            commit_content['parent'] = parent
        if parent2:
            commit_content['merged_parent'] = parent2
        sha1 = hashlib.sha1(json.dumps(commit_content).encode()).hexdigest()
        if not os.path.exists(repo_path("objects",sha1[:2])):
            os.makedirs(repo_path("objects",sha1[:2]))
        with open(repo_path("objects",sha1[:2],sha1[2:]),"wb") as file:
            file.write(zlib.compress(json.dumps(commit_content).encode()))
        with open(index_file_path,"w") as file:
            json.dump({},file)
        update_head(sha1)
        print(f"Successfully committed files with {sha1} --> {commit_message}")
    except Exception as ex:
        raise ex

def get_head():
    try:
        head = None
        head_path = repo_path("HEAD")
        if not os.path.exists(head_path):
            raise Exception("No HEAD")
        head_branch = None
        with open(head_path,"r") as file:
            head_branch = file.read().strip()
        if head_branch.startswith("ref:"):
            head_branch = head_branch.split()
            if not os.path.exists(repo_path(head_branch[1])):
                with open(repo_path(head_branch[1]),"w") as file:
                    file.write(" ")
            with open(repo_path(head_branch[1]),"r") as file:
                head = file.read().strip()
        return head
    except Exception as ex:
        raise ex

def update_head(commit):
    try:
        head_path = repo_path("HEAD")
        with open(head_path,"r") as file:
            head_content = file.read()
        if head_content.startswith("ref:"):
            head_content = head_content.split()
            with open(repo_path(head_content[1]),"w") as file:
                file.write(commit)
    except Exception as ex:
        raise ex
    
def log(all_parents=False,one_line=False):
    try:
        parent_commit = get_head()
        visited = set()
        queue = deque([parent_commit])
        while queue:
            current_commit = queue.popleft()
            if current_commit in visited:
                continue
            visited.add(current_commit)
            with open(repo_path("objects",current_commit[:2],current_commit[2:]),"rb") as file:
                content = zlib.decompress(file.read())
                content = content.decode(chardet.detect(content)['encoding'])
                content = json.loads(content)
                if one_line:
                    print(f"\n{current_commit} : {content['message']}")
                else:
                    print(f"\nCommit : {current_commit}\nDate : {content['date']}\nUser : {content['username']}<{content['email']}>\n")
                    if 'merged_parent' in content:
                        print(f"\nMerged : {content['merged_parent']}")
                    print(f"\n\n{content['message']}")

                if all_parents:
                    if 'parent' in content:
                        queue.append(content['parent'])
                    elif 'merged_parent' in content:
                        queue.append(content['merged_parent'])
                else:
                    if 'parent' in content:
                        queue.append(content['parent'])
                
    except Exception as ex:
        raise ex

def get_commit_hashes():
    try:
        head = get_head()
        commit_hashes = []
        while head:
            with open(repo_path("objects",head[:2],head[2:]),"rb") as file:
                content = zlib.decompress(file.read())
                content = content.decode(chardet.detect(content)['encoding'])
                content = json.loads(content)
                commit_hashes.extend(list(content['tree'].values()))
                head = content['parent'] if 'parent' in content else None
        return commit_hashes
    except Exception as ex:
        raise ex
    
def file_list(filelist=[]):
    try:
        if len(filelist) == 0:
            file_list = [file for file in os.listdir() if not os.path.isdir(file)]
        else:
            file_list = filelist
        file_to_ignore = []
        if os.path.exists(repo_path(".microgitignore")):
            ignorefilelist = []
            with open(repo_path(".microgitignore"),"r") as file:
                ignorefilelist = file.readlines()
            for file in ignorefilelist:
                file_to_ignore.extend(fnmatch.filter(file_list,file.strip()))
        return list(set(file_list) - set(file_to_ignore))
    except Exception as ex:
        raise ex
    
def checkout(commithash_or_branchname):
    try:
        checkout_to_branch = False
        if os.path.exists(repo_path("refs","heads",commithash_or_branchname)):
            with open(repo_path("refs","heads",commithash_or_branchname),"r") as file:
                commithash = file.read().strip()
                checkout_to_branch = True
            with open(repo_path("HEAD"),"w") as file:
                file.write(f"ref: refs/heads/{commithash_or_branchname}")
        else:
            commithash = commithash_or_branchname   
        if not os.path.exists(repo_path("objects",commithash[:2],commithash[2:])):
            raise Exception(f"Commit hash or branch not found : {commithash_or_branchname}")
        with open(repo_path("objects",commithash[:2],commithash[2:]),"rb") as file:
            content = zlib.decompress(file.read())
            content = content.decode(chardet.detect(content)['encoding'])
            content = json.loads(content)
        all_files = file_list()
        for file in all_files:
            if file not in list(content['tree'].keys()):
                os.remove(file)
        for filename,commit in content['tree'].items():
            with open(filename,"w") as f_out:
                f_out.write(cat_file(commit))
        print(f"Switched to {'commit' if not checkout_to_branch else 'branch'} {commithash_or_branchname}")
    except Exception as ex:
        raise ex
    
def branch(branch_name):
    try:
        if branch_name is None:
            if not os.path.exists(repo_path("refs","heads")):
                raise Exception("branch path (refs/heads) not found")
            with open(repo_path("HEAD"),"r") as file:
                head_branch_name = file.read().strip().split()[1]
                head_branch_name = head_branch_name.split("/")[2] if "/" in head_branch_name else None
            for files in os.listdir(repo_path("refs","heads")):
                    print(f"{'* ' if files == head_branch_name else ''}{files}")
        else:
            head = get_head()
            if not os.path.exists(repo_path("refs","heads",branch_name)):
                with open(repo_path("refs","heads",branch_name),"w") as file:
                    file.write(head)
                print(f"Created branch '{branch_name}'")
            else:
                print(f"Branch {branch_name} already exists")
    except Exception as ex:
        raise ex
def get_branch_name():
    try:
        content = None
        branch_name = ''
        if not os.path.exists(repo_path("HEAD")):
            raise Exception("HEAD file not found")
        with open(repo_path("HEAD"),"r") as file:
            content = file.read().split()
            branch_name = content[1].split("/")[2]
        return branch_name
    except Exception as ex:
        raise ex
def status():
    try:
        staged_files = {}
        to_be_staged_files = []
        unstaged_files = []
        print(f"On branch {get_branch_name()}")
        if not os.path.exists(repo_path("index")):
            raise Exception("No index file")
        with open(repo_path("index"),"r") as file:
            staged_files = json.load(file)
        if len(staged_files) > 0:
            print("\nStaged changes\n---------------------------------------")
            for files in staged_files:
                print(files)
            for file,commit_hash in staged_files.items():
                if commit_hash != hash_object(file):
                    to_be_staged_files.append(f"Modified : {file}")
            if len(to_be_staged_files) > 0:
                print("\nChanges to be staged\n---------------------------------------------")
                for files in to_be_staged_files:
                    print(files)

        file_commits = get_commit_hashes()
        files = file_list()
        for file in files:
            if hash_object(file) not in file_commits and file not in staged_files:
                unstaged_files.append(file)
        if len(unstaged_files) > 0:
            print("\nUntracked files(use microgit.py add <filename> to add)\n----------------------------------")
            for files in unstaged_files:
                    print(files)
    except Exception as ex:
        raise ex

def merge(branch_name):
    try:
        conflict_detected = False
        if not os.path.exists(repo_path("refs","heads",branch_name)):
            raise Exception(f"branch '{branch_name}' does not exist")
        if not os.path.exists(repo_path("HEAD")):
            raise Exception("No HEAD file")
        head_branch_commit = get_head()
        merge_branch_commit = None
        with open(repo_path("refs","heads",branch_name),"r") as file:
            merge_branch_commit = file.read().strip()
        head_files = []
        files_to_merge = []
        merge_list = {}
        if not os.path.exists(repo_path("objects",head_branch_commit[:2],head_branch_commit[2:])):
            raise Exception("HEAD commit does not exist")
        with open(repo_path("objects",head_branch_commit[:2],head_branch_commit[2:]),"rb") as file:
            content = zlib.decompress(file.read())
            content = content.decode(chardet.detect(content)['encoding'])
            content = json.loads(content)
            head_files = content['tree']
        if not os.path.exists(repo_path("objects",merge_branch_commit[:2],merge_branch_commit[2:])):
            raise Exception("merge branch commit does not exist")
        with open(repo_path("objects",merge_branch_commit[:2],merge_branch_commit[2:]),"rb") as file:
            content = zlib.decompress(file.read())
            content = content.decode(chardet.detect(content)['encoding'])
            content = json.loads(content)
            files_to_merge = content['tree']
        all_files = set(head_files.keys()) | set(files_to_merge.keys())
        for filename in all_files:
            head_hash = head_files.get(filename,None)
            branch_hash = files_to_merge.get(filename,None)

            if head_hash == branch_hash:
                merge_list[filename] = head_hash
            elif not head_hash and branch_hash:
                merge_list[filename] = branch_hash
            elif head_hash and not branch_hash:
                merge_list[filename] = head_hash
            else:
                conflict_detected = True
                content = "\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<HEAD\n"+cat_file(head_hash)+"\n===========================\n"+cat_file(branch_hash)+f"\n>>>>>>>>>>>>>>>>>>>>>>>>>>>{branch_name}\n"
                with open(filename,"w") as file:
                    file.write(content)
                merge_list[filename] = hash_object(filename)
            add(list(merge_list.keys()))
            commit(f"Merged feature branch '{branch_name}'",parent2 = branch_hash)
            print(f"Successfully Merged feature branch '{branch_name}' {'With conflicts.\nTry to resolve it manually' if conflict_detected else ''}")
    except Exception as ex:
        raise ex