import pod
import pod.list
import os
import re

from fs.opener import fsopendir
from fs.utils import copyfile
from copy import deepcopy

class Enumerate(object):
    def __init__(self, names):
        for number, name in enumerate(names.split()):
            setattr(self, name, number)

PathStatus=Enumerate("undef include ignore stop")

class PathPart(pod.Object):
    def __init__(self, name, parent= None, lPathStatus=PathStatus.undef, depth= 0):
        pod.Object.__init__(self)
        
        self.name= name
        self.PathStatus= lPathStatus
        
        self.children= []
        self.parent= parent
        if parent!=None:
            self.parent.children.append(self)
        self.depth= depth
                
    def CreatePath(self, path, lPathStatus= PathStatus.undef):
        if(path==[]):
            return self
        
        tpathPart=PathPart(path[0], self, lPathStatus, self.depth+1)
        
        return tpathPart.CreatePath(path[1:])   
        
    def GetPathPart(self, path, new=False):
        if(path==[]):
            return self.parent
        if(self.name!=path[0]):
            return None
            
        for child in self.children:
            tpathPart= child.GetPathPart(path[1:], new)
            if(tpathPart!=None):
                return tpathPart
            
        if(new == True):
            return self.CreatePath(path[1:])
        
        return self
        
    def GetLastPart(self, path):
        if(path==[]):
            return self.parent
        match1= re.match('^\{(?P<regex>\S+)\}$',self.name)
        match2= re.match('^\|(?P<regex>\S+)\|$',self.name)
        if match1:
            regex= match1.group('regex')
            if not re.match(regex, path[0]):
                return None
        elif match2:
            regex= match2.group('regex')
            stringpath= '/'.join(path)
            splited= re.split(regex, stringpath,1)
            if splited[0]!=stringpath and len(stringpath)>len(splited[1]):
                path= splited[1].split("/")
            else:
                return None
        elif(self.name!=path[0]):
            return None
            
        for child in self.children:
            tpathPart= child.GetLastPart(path[1:])
            if(tpathPart!=None):
                return tpathPart
            
        return self
        
    def DelPathPart(self, path):
        tpathPart= self.GetPathPart(path, False)
        if(tpathPart==None):
            return
        
        tpathPart.parent.children.remove(tpathPart)
        tpathPart.delete()
        
    def SetPathStatus(self, path, lPathStatus):
        path_part= self.GetPathPart(path, True)
        path_part.PathStatus = lPathStatus
        
    def GetPathStatus(self, path):
        tpathPart= self.GetLastPart(path)
        
        if(tpathPart==None):
            return PathStatus.undef
            
        return tpathPart.PathStatus
    
    def __str__(self):
        absolute_path= '/'.join(self.AbsolutePath())
        if self.PathStatus==PathStatus.ignore:
            str_status= "ignore"
        elif self.PathStatus==PathStatus.include:
            str_status= "include"
        elif self.PathStatus==PathStatus.stop:
            str_status= "stop"
        elif self.PathStatus==PathStatus.undef:
            str_status= "undef"
        return absolute_path + " [" + str_status + "]"
    
    def AbsolutePath(self):
        path=[self.name]
        parent= self.parent
        while parent:
            path.append(parent.name)
            parent= parent.parent
        path.reverse()
        return path 
        
    def pre_delete(self):
        for child in self.children:
            child.delete()
            break
        
    def __deepcopy__(self, memo):
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing
         
        dup= None
        if self.parent:
            dup= PathPart(self.name, deepcopy(self.parent, memo), deepcopy(self.PathStatus, memo), deepcopy(self.depth, memo))
        else:
            dup= PathPart(self.name, None, deepcopy(self.PathStatus, memo), deepcopy(self.depth, memo))
            
        return dup
            
class ConfigLayer(pod.Object):
    def __init__(self, name, FileAccess, lPathStatus, parent=None):
        pod.Object.__init__(self)
        
        self.name= name
        self.parent= parent
        self.children= []
        if parent:
            self.parent.children.append(self)
        self.FileAccess= FileAccess
        self.paths= PathPart("root")
        self.paths.PathStatus= lPathStatus
        
    def GetPathStatus(self, path):
        depth= len(path)
        tpathPart= self.paths.GetLastPart(path)
        if(tpathPart.PathStatus==PathStatus.stop):
            return PathStatus.stop
        if(tpathPart.PathStatus==PathStatus.undef):
            return self.__GetPathStatus__(path, self, self.paths, depth)
        else:
            return self.__GetPathStatus__(path, self, tpathPart, depth)
        
    def __GetPathStatus__(self, path, parent, previousBest, depth):
        if(parent.parent==None):
            return previousBest.PathStatus
        
        tpathPart= parent.parent.paths.GetLastPart(path)
        
        'If we must stop at speciffic path then return status to stop'
        if(tpathPart.PathStatus==PathStatus.stop):
            return PathStatus.stop
        
        'if path status is not defined go to next parent'
        if(tpathPart.PathStatus==PathStatus.undef):
            return self.__GetPathStatus__(path, parent.parent, previousBest, depth)
        
        sum1= depth-previousBest.depth
        sum2= depth-tpathPart.depth
        
        if( sum2>0 and sum2<sum1):
            previousBest= tpathPart
            
        if(parent.parent.parent==None):
            return previousBest.PathStatus;
            
        return self.__GetPathStatus__(path, parent.parent, previousBest, depth)
    
    def GetConfigByPath(self, path):
        if self.name != path[0]:
            return None
        
        if len(path)>1:
            for child in self.children:
                if child.GetConfigByPath(path[1:]):
                    return child
        else:
            return self
            
        return None
    
    def GetConfigByName(self, name):
        if self.name != name:
            if self.children:
                for child in self.children:
                    cfg= child.GetConfigByName(name)
                    if cfg: return cfg
            else:
                return None
            
        return self
    
    def GetRootConfigLayer(self):
        parent= self.parent
        last_parent= self
        while parent:
            last_parent= parent
            parent= parent.parent
            
        return last_parent
        
    def pre_delete(self):
        #Only delete first child
        for child in self.children:
            child.delete()
            break
        
        self.paths.delete()
        
    def __deepcopy__(self, memo):
        not_there = []
        existing = memo.get(self, not_there)
        if existing is not not_there:
            return existing
         
        dup= None
        if self.parent:
            dup= ConfigLayer(self.name+"_copy", None, deepcopy(self.paths.PathStatus, memo), deepcopy(self.parent, memo))
        else:
            dup= ConfigLayer(self.name+"_copy", None, deepcopy(self.paths.PathStatus, memo), None)
            
        dup.paths= deepcopy(self.paths, memo)
            
        return dup
        
class ConfigLayerManager(pod.Object):
    '''
    Stores layer configurations.
    All created configurations goes here, so they can be reusable in
    many FileSyncConfig-s. Config layers should never be deleted from
    FileSyncConfig, because it's just the object who uses them.
    '''
    
    def __init__(self):
        pod.Object.__init__(self)
        
        self.configs= []
        
    def RootAdd(self, config):
        root= config.GetRootConfigLayer()
        if root not in self.configs:
            self.configs.append(root)        
        
    def NewConfig(self, *args, **kwargs):
        '''
        Adds new config layer, same parameters as ConfigLayer
        '''
        config = ConfigLayer(*args, **kwargs)
        self.RootAdd(config)
        
        return config
        
    def AddConfig(self, *configs):
        '''
        Adds config layers
        @param config: Multiple configs
        @type config: ConfigLayer[]
        '''
        for config in configs:
            #Dont add config if config with the same name exists
            if self.GetConfigByName(config.name):
                return False
            self.RootAdd(config)
            
        return True
        
    def GetConfigByName(self, name):
        '''
        Gets config my name.
        @param name: Config name
        @type name: Stringself
        '''
        if name==None:
            return None
        
        name_parts= name.split("->")
        
        possible_cfg= None
        for config in self.configs:
            cfg= config.GetConfigByPath(name_parts)
            if cfg:
                return cfg
            # we search for fist occurence
            elif len(name_parts)==1 and not possible_cfg:
                possible_cfg= config.GetConfigByName(name)
        
        return possible_cfg
    
    def DuplicateConfig(self, config):
        dup= deepcopy(config)
        self.AddConfig(dup)
        
    def RemoveConfig(self, config):
        '''
        Removes config layer. Also removes all sub-config layers
        that depend on this config.
        @param config: Configuration
        @type config: ConfigLayer
        '''       
        if not config: return 
        config= config.GetRootConfigLayer()
        if config in self.configs:
            self.configs.remove(config)
            config.delete()
            
    def GetRootConfigs(self):
        return self.configs
        
    def pre_delete(self):
        '''
        Erases all config layers.
        '''
        for config in self.configs:
            config.delete()
            break
        
class FileSyncConfig(pod.Object):
    def __init__(self, source_path, dest_path, config_layer, name=None):
        '''
        init
        @param source_path: Path to source used by pyfileaccess fsopendir
        @type source_path: String
        @param dest_path: Path to dest used by pyfileaccess fsopendir
        @type dest_path: String
        @param config_layer: Config layer to use
        @type config_layer: ConfigLayer
        '''
        pod.Object.__init__(self)
        
        self.source_path = source_path
        self.dest_path = dest_path
        self.config_layer = config_layer
        self.name= name
        
    def __str__(self):
        return "name:'%s', src:'%s', dst:'%s', config:'%s'" \
             % (self.name, self.source_path, self.dest_path, self.config_layer.name)
        
class FileSyncConfigManager(pod.Object):
    def __init__(self):
        pod.Object.__init__(self)
        self.configs= []
        
    def AddConfig(self, config):
        if self.GetConfigByName(config.name):
            return False
        self.configs.append(config)
        
        return True
        
    def RemoveConfig(self, config):
        self.configs.remove(config)
        config.delete()
        
    def GetConfigByName(self, name):
        for config in self.configs:
            if config.name==name:
                return config
        
class FileSync(object):
    def __init__(self, file_sync_config):
        '''
        init
        @param file_sync_config: Confg to use with synch.
        @type file_sync_config: FileSyncConfig
        '''
        self.file_sync_config = file_sync_config
        
    def sync(self, base_path= ["root"], verbose=True):
        if(self.file_sync_config.source_path):
            try:
                src= fsopendir(self.file_sync_config.source_path)
            except fs.opener.OpenerError, fs.opener.NoOpenerError:
                print "Error opening %s!" % (self.file_sync_config.source_path)
        else:
            return
        if(self.file_sync_config.dest_path):
            try:
                dst= fsopendir(self.file_sync_config.dest_path)
            except fs.opener.OpenerError, fs.opener.NoOpenerError:
                print "Error opening %s!" % (self.file_sync_config.dest_path)
        else:
            return
        
        self._synch_walk(src, dst, base_path)
        self._synch_walk(dst, src, base_path)
        
    def _synch_walk(self, src, dst, path, depth= 0,verbose=True):
        src_files= src.listdir()
        dst_files= dst.listdir()
        config= self.file_sync_config.config_layer
        for file in src_files:
            status= config.GetPathStatus(path+[file])
            if verbose: print "\t"*depth+"Object: "+file
            if src.isdir(file):
                if status==PathStatus.include or status==PathStatus.ignore:
                    if verbose: print "\t"*depth+"dir_enter->"
                    new_src= src.makeopendir(file)
                    new_dst= dst.makeopendir(file)
                    self._synch_walk(new_src, new_dst, path[:]+[file], depth+1)
                    if verbose: print "\t"*depth+"<-dir_leave"
                if status==PathStatus.stop:
                    if verbose: print "\t"*depth+"Removing dir"
                    src.removedir(file, force=True)
            if src.isfile(file):
                if status==PathStatus.include:
                    if file in dst_files:
                        if verbose: print "\t"*depth+"Synching file"
                        src_mtime= src.getinfo(file)["modified_time"]
                        dst_mtime= dst.getinfo(file)["modified_time"]

                        if src_mtime>dst_mtime:
                            copyfile(src, file, dst, file)
                        elif src_mtime==dst_mtime:
                            print "\t"*depth+"Nothing to synch."
                        else:
                            copyfile(dst, file, src, file)
                    else:
                        copyfile(src, file, dst, file)
                if status==PathStatus.stop or status==PathStatus.ignore:
                    if verbose: print "\t"*depth+"Removing file"
                    src.remove(file)
                    