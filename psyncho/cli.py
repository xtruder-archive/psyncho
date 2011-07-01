#!/home/offlinehacker/projects/UnisonConfig/bin/python
import os

from optparse import OptionParser

from lib.command import PsynchoCommand

def main():
    usage = "usage: psyncho [options] args"
    parser = OptionParser(usage)
    parser.add_option("--config", dest="config_file",
                      help="path to config file")
    parser.add_option("--new-config-layer",
                      help="Adds new config layer, args: name , [root_path_status], [parent_name]", action="store_true", dest="new_config_layer")
    parser.add_option("--select-config-layer",
                      help="Selects current config layer, args: name", action="store_true", dest="select_config_layer")
    parser.add_option("--del-config-layer",
                      help="Deletes config layer, args: name", action="store_true", dest="del_config_layer")
    parser.add_option("--rename-config-layer",
                      help="Deletes config layer, args: name", action="store_true", dest="rename_config_layer")
    parser.add_option("--dup-config-layer",
                      help="Duplicates config layer, args: name", action="store_true", dest="dup_config_layer")
    parser.add_option("--print-config-layers",
                      help="Prints config layers.", action="store_true", dest="print_config_layers")
    parser.add_option("--set-path-status",
                      help="Sets path startus, args: path, status", action="store_true", dest="set_path_status")
    parser.add_option("--get-path-status",
                      help="Gets path startus, args: path", action="store_true", dest="get_path_status")
    parser.add_option("--del-path-status",
                      help="Deletes path startus, args: path", action="store_true", dest="del_path_status")
    parser.add_option("--new-synch",
                      help="Adds new synch, args: name, src, dst, [config_name]", action="store_true", dest="new_synch")
    parser.add_option("--print-synch",
                      help="Prints all synch configs.", action="store_true", dest="print_synch")
    parser.add_option("-s", "--synch",
                      help="Starts sync, args: name, [base_path]", action="store_true", dest="synch")
    parser.add_option("-i", "--init",
                      help="Initializes sync in current folder, args: name", action="store_true", dest="init")
    parser.add_option("-a", "--add",
                      help="Initializes sync in current folder, args: name, path, status", action="store_true", dest="add")
    
    (options, args) = parser.parse_args()
    ps= None
    if options.config_file:
        ps= PsynchoCommand(options.config_file)
    else:
        ps= PsynchoCommand()
        
    if options.new_config_layer and len(args)>0:
        name= args[0]
        root_status="include"
        parent_config_name= None
        if len(args)>1:
            root_status= args[1]
        if len(args)>2:
            parent_config_name= args[2]
        ps.NewConfig( name, root_status, parent_config_name )  
    elif options.select_config_layer and len(args)>0:
        name= args[0]
        ps.SelectCurrentConfig(name)
    elif options.del_config_layer and len(args)>0:
        name= args[0]
        ps.DelConfig(name)
    elif options.dup_config_layer and len(args)>0:
        name= args[0]
        ps.DuplicateConfig(name)
    elif options.rename_config_layer and len(args)>1:
        old_name= args[0]
        new_name= args[1]
        ps.RenameConfig(old_name, new_name)
    elif options.print_config_layers:
        print ps.GenConfigTree(True)
    elif options.set_path_status and len(args)>2:
        path= args[0]
        status= args[1]
        config_name= args[2]
        ps.SetPathStatus(path, status, config_name)
    elif options.get_path_status and len(args)>1:
        path= args[0]
        config_name= args[1]
        print ps.GetPathStatus(path, config_name)
    elif options.del_path_status and len(args)>1:
        path= args[0]
        config_name= args[1]
        ps.DelPathStatus(path, config_name)
    elif options.new_synch and len(args)>3:
        name= args[0]
        src= args[1]
        dst= args[2]
        config_name= args[3]
        ps.NewSynch( name, src, dst, config_name )  
    elif options.print_synch:
        print ps.GenSynchList()
    elif options.synch and len(args)>0:
        name= args[0]
        path= "root"
        if len(args)>1:
            path= args[1]
        ps.Synch(name, path)
    elif options.init:
        open('.psyncho', 'w').close() 
    elif options.add and len(args)>2:
        name= args[0]
        path= args[1]
        status= args[2]
        
        curr_path= os.path.abspath(os.getcwd())
        sub_path= curr_path.split("/")[-1:]
        old_path=[""]
        while True:
            files= os.listdir(curr_path)
            if ".psyncho" in files:
                break
            curr_path= os.path.abspath(os.path.join(curr_path, '../'))
            old_path= sub_path
            sub_path+= curr_path.split("/")[-1:]
            
        sub_path.reverse()
        print "/".join(old_path)+path
        ps.SetPathStatus("root/"+"/".join(old_path)+path, status, name)
        
    ps.Save()
        
if __name__ == "__main__":
    main()
        
