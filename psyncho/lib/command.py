from psyncho import *

class PsynchoCommand(object):
    def __init__(self, db_file="psyncho_config.db"):        
        self.db = pod.Db(file = db_file, dynamic_index = True)
        self.config_mgr=None
        self.fs_mgr=None
        
        for self.config_mgr in ConfigLayerManager: break
        if self.config_mgr==None:
            self.config_mgr= ConfigLayerManager()
            
        for self.fs_mgr in FileSyncConfigManager: break
        if self.fs_mgr==None:
            self.fs_mgr= FileSyncConfigManager()
        
        self.current_config= None
            
    def _StatusFromString(self, string_status):
        path_status= None
        if(string_status=="include"):
            path_status= PathStatus.include
        elif(string_status=="ignore"):
            path_status= PathStatus.ignore
        elif(string_status=="stop"):
            path_status= PathStatus.stop
        return path_status
    
    def _StatusToString(self, status):
        if status==PathStatus.include:
            return "include"
        elif status==PathStatus.ignore:
            return "ignore"
        elif status==PathStatus.stop:
            return "stop"
        return "undef"           
    
    def Save(self):
        self.db.commit()  
        
    def NewSynch(self, name, source_path, dest_path, config_name=None):
        if not config_name:
            config= self.current_config
        else:
            config= self.config_mgr.GetConfigByName(config_name)
            
        self.fs_mgr.AddConfig(FileSyncConfig(source_path, dest_path, config, name))
        
    def Synch(self, name, base_path_string="root"):
        fsc= self.fs_mgr.GetConfigByName(name)
        if not fsc:
            return None
        
        base_path=base_path_string.split("/")
        fs= FileSync(fsc)
        fs.sync(base_path)
        
    def NewConfig(self, config_name, root_path_status, parent_config_name=None):
        path_status= self._StatusFromString(root_path_status)
        parent= self.config_mgr.GetConfigByName(parent_config_name)
        config= self.config_mgr.NewConfig(config_name, None, path_status, parent)
        self.current_config= config
        
        return config

    def DelConfig(self, config_name):
        config= self.config_mgr.GetConfigByName(config_name)
        self.config_mgr.RemoveConfig(config)
        
    def RenameConfig(self, old_name, new_name):
        config= self.config_mgr.GetConfigByName(old_name)
        config.name= new_name
        
    def DuplicateConfig(self, config_name):
        config= self.config_mgr.GetConfigByName(config_name)
        self.config_mgr.DuplicateConfig(config)
        
    def SelectCurrentConfig(self, config_name):
        self.current_config= self.config_mgr.GetConfigByName(config_name)
        
    def SetPathStatus(self, string_path, string_status, config_name=None):
        config= self.current_config
        if (not config) and (not config_name):
            return False
        if config_name:
            config= self.config_mgr.GetConfigByName(config_name)
            if not config:
                return
            
        status= self._StatusFromString(string_status)
        path= string_path.split("/")
        
        config.paths.SetPathStatus(path, status)
        
    def GetPathStatus(self, string_path, config_name=None):
        config= self.current_config
        if (not config) and (not config_name):
            return False
        if config_name:
            config= self.config_mgr.GetConfigByName(config_name)
            
        path= string_path.split("/")
        return self._StatusToString(config.GetPathStatus(path))
    
    def DelPathStatus(self, string_path, config_name=None):
        config= self.current_config
        if (not config) and (not config_name):
            return False
        if config_name:
            config= self.config_mgr.GetConfigByName(config_name)
            
        path= string_path.split("/")
        
        config.paths.DelPathPart(path)
        
    def ClearIndexes(self, name):
        fsc= self.fs_mgr.GetConfigByName(name)
        if not fsc:
            return None
        
        fsc.ClearIndexes()
    
    def GenSynchList(self):
        out= "Synch configs:"
        for synch in self.fs_mgr.configs:
            out+= "-> " + synch.__str__() + "\n"
            
        return out      
        
    def GenPathList(self, config, depth):
        return self._GenPathListRecursive(depth, config.paths, "")
        
    def _GenPathListRecursive(self, depth, path, out):
        if path.PathStatus!=PathStatus.undef:
            out+="\t"*depth+"->"+path.__str__()+"\n"
        for sub_path in path.children:
            out=self._GenPathListRecursive(depth, sub_path, out)
            
        return out
        
    def GenConfigTree(self, paths=False):
        out=""
        for config in self.config_mgr.GetRootConfigs():
            out+= config.name+ "\n"
            if(paths):
                out+= "->Paths:\n"
                out+= self.GenPathList(config, 1)
            out= self._GenConfigTree(out, config, 1, paths)
            
        return out
            
    def _GenConfigTree(self, out, config, depth, paths= False):
        for children in config.children:
            out+= "\t" * depth+ children.name+ "\n"
            if(paths):
                out+= "\t"*(depth)+"->Paths:\n"
                out+= self.GenPathList(children, depth+1)
            out= self._GenConfigTree(out, children, depth+1, paths)
        return out