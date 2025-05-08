import argparse
import helpers


parser = argparse.ArgumentParser(description="A Simple microgit command line tool")
sub_parser = parser.add_subparsers(dest="git_command")

init_command = sub_parser.add_parser("init",help="Initialize a git repository")
init_command.set_defaults(func=helpers.init)

hash_object = sub_parser.add_parser("hash-object",help="Hash given file")
hash_object.add_argument("file")
hash_object.set_defaults(func=helpers.hash_object)

cat_file = sub_parser.add_parser("cat-file",help="Return contents of file hash")
cat_file.add_argument("hash")
cat_file.set_defaults(func=helpers.cat_file)

add_file = sub_parser.add_parser("add",help="To add file to the git repository")
add_file.add_argument("filename",nargs="+")
add_file.set_defaults(func=helpers.add)

commit_file = sub_parser.add_parser("commit",help="Commit files added using 'add' command")
commit_file.add_argument("--message","-m",required=True,type=str)
commit_file.set_defaults(func=helpers.commit)

log_files = sub_parser.add_parser("log",help="To get commit logs")
log_files.set_defaults(func=helpers.log)

checkout_command = sub_parser.add_parser("checkout",help="Checkout to a particular commit hash or to a tag name or to another branch")
checkout_command.add_argument("commithash",help="Commit hash/branch/tagname")
checkout_command.set_defaults(func=helpers.checkout)

branch_command = sub_parser.add_parser("branch",help="Create or list branches")
branch_command.add_argument("branchname",nargs="?",help="Name of branch")
branch_command.set_defaults(func=helpers.branch)

if __name__ == "__main__":
    try:
        arguments = parser.parse_args()
        if arguments.git_command == "init":
            arguments.func()
        elif arguments.git_command == "hash-object":
            print(arguments.func(arguments.file))
        elif arguments.git_command == "cat-file":
            print(arguments.func(arguments.hash))
        elif arguments.git_command == "add":
            arguments.func(arguments.filename)
        elif arguments.git_command == "commit":
            arguments.func(arguments.message)
        elif arguments.git_command == "log":
            arguments.func()
        elif arguments.git_command == "checkout":
            arguments.func(arguments.commithash)
        elif arguments.git_command == "branch":
            arguments.func(arguments.branchname)
    except Exception as ex:
        print(f"{str(ex)}")