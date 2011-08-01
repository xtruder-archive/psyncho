import unittest
import pat  # touch pat.py in the cwd and try to import the empty file under Linux

from fs.opener import fsopendir
from copy import deepcopy

from extra import Enumerate, is_file, is_lnk, is_dir
from command import PsynchoCommand
from psyncho import *

ObjectType= Enumerate("link dir file")

class TestSynch(unittest.TestCase): 
    @classmethod
    def setUpClass(cls):
        cls.cmd= PsynchoCommand()
        
    def OpenDir(self, f, root, dir):
        f.makeopendir(root+"/"+dir, recursive=True)
        
    def CreateFile(self, f, root, dir):
        f.makeopendir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True)
        f.createfile(root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
        
    def CreateLink(self, f, root, dir, linkto):
        f.makeopendir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True)
        f.symlink(linkto, root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
        
    def RemoveDir(self, f, root, dir):
        f.removedir(root+"/"+dir, recursive=True, force=True)
        
    def RemoveFile(self, f, root, dir):
        f.remove(root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
        f.removedir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True, force=True)
        
    def RemoveLink(self, f, root, dir):
        f.remove(root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
        f.removedir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True, force=True)    
        
    def MakeObjects(self, path, root, objects):
        f= fsopendir(path)
        for type, object, attr in objects:
            if type==ObjectType.dir:
                self.OpenDir(f, root, object)
            elif type==ObjectType.file:
                self.CreateFile(f, root, object)
            elif type==ObjectType.link:
                self.CreateLink(f, root, object, attr)
                
    def DelObjects(self, path, root, objects):
        f= fsopendir(path)
        for type, object, attr in objects:
            if type==ObjectType.dir:
                self.RemoveDir(f, root, object)
            elif type==ObjectType.file:
                self.RemoveFile(f, root, object)
            elif type==ObjectType.link:
                self.RemoveLink(f, root, object, attr)
            
    def CheckObjects(self, path, root, objects, correct_objects):
        f= fsopendir(path)
        for type, object, attr in objects:
            try: i= f.getinfo(root+"/"+object)
            except:
                self.assertTrue(object not in correct_objects)
                continue
            if is_dir(i) and type==ObjectType.dir:
                self.assertTrue(object in correct_objects)
            elif is_file(i) and type==ObjectType.file:
                self.assertTrue(object in correct_objects)
            elif is_lnk(i) and type==ObjectType.link:
                self.assertTrue(object in correct_objects)
            
    def CurrentDir(self):
        PAT=str(pat).split()[3][1:-9] # PATH extracted..
        return PAT
        
    def test_ConfigTreeOutput(self):
        print self.cmd.GenConfigTree()
        self.cmd.NewConfig("test", "include", None)
        self.cmd.NewConfig("test2", "include", "test")
        self.cmd.NewConfig("test3", "include", "test")
        self.cmd.NewConfig("test4", "include", "test3")
        a=self.cmd.GenConfigTree()
        self.assertEqual("test\n\ttest2\n\ttest3\n\t\ttest4\n",a)
        
        self.cmd.DelConfig("test")
        
    def test_pathsOutput(self):
        conf1= self.cmd.NewConfig("test", "include", None)
        conf1.paths.SetPathStatus(["root","jaka","hudoklin","cba"], PathStatus.stop)
        conf1.paths.SetPathStatus(["root","jaka","hudoklin"], PathStatus.ignore)
        conf2= self.cmd.NewConfig("test2", "ignore", "test")
        conf2.paths.SetPathStatus(["root","micka"], PathStatus.include)
        a=self.cmd.GenPathList(conf2,0)
        self.assertEqual("->root [ignore]\n->root/micka [include]\n", a)
        
        a=self.cmd.GenConfigTree(True)
        print a
        
        self.cmd.DelConfig("test")
        
    def test_pathStatus(self):
        self.cmd.NewConfig("test", "include", None)
        self.cmd.SelectCurrentConfig("test")
        self.cmd.SetPathStatus("root/jaka/hudoklin/cba", "include")
        self.assertEqual(self.cmd.GetPathStatus("root/jaka/hudoklin/cba"),"include")
        
        self.cmd.DelConfig("test")
        
    def test_Synch(self):
        dirs1=[(ObjectType.file, "a/m/file.txt", None), \
               (ObjectType.file, "a/file.txt", None), \
               (ObjectType.file, "b/c/file.txt", None), \
               (ObjectType.dir, "c", None)]
        dirs2=[(ObjectType.dir, "", None)]
        
        self.MakeObjects(self.CurrentDir()+"/testdirs","test1",dirs1)
        self.MakeObjects(self.CurrentDir()+"/testdirs","test2",dirs2)
        self.cmd.NewConfig("test", "include", None)
        self.cmd.SelectCurrentConfig("test")
        self.cmd.SetPathStatus("root/a", "ignore")
        self.cmd.SetPathStatus("root/b", "include")
        self.cmd.SetPathStatus("root/c", "stop")
        self.cmd.NewConfig("test2", "include", "test")
        self.cmd.SelectCurrentConfig("test2")
        self.cmd.SetPathStatus("root/a/m/file.txt", "include")
        self.cmd.SetPathStatus("root/a/file.txt", "include")
        self.cmd.SetPathStatus("root/b/c/file.txt", "include")
        
        self.cmd.NewConfig("test2", "include", "test->test2")
        print self.cmd.GenConfigTree(True)
        
        self.cmd.NewSynch("synchtest1","./testdirs/test1", "./testdirs/test2", "test2")
        self.cmd.Synch("synchtest1") 
        
        correct_dirs=["a/m/file.txt","b/c", "a/file.txt", "b/c/file.txt"]
        self.CheckObjects(self.CurrentDir()+"/testdirs","test1",dirs1,correct_dirs)
        self.CheckObjects(self.CurrentDir()+"/testdirs","test2",dirs1,correct_dirs)
        
        self.DelObjects(self.CurrentDir()+"/testdirs","test1",[(ObjectType.dir, "", None)])
        self.DelObjects(self.CurrentDir()+"/testdirs","test2",[(ObjectType.dir, "", None)])
        
        self.cmd.DelConfig("test")
        self.cmd.DelConfig("test2")
        
    def test_regex(self):
        conf1= self.cmd.NewConfig("test", "include", None)
        #First rule overrides second
        conf1.paths.SetPathStatus(["root","jaka","{hudoklin|micka}","{cba|cde}"], PathStatus.stop)
        conf1.paths.SetPathStatus(["root","jaka","micka","cde"], PathStatus.include)
        result= conf1.paths.GetPathStatus(["root","jaka","hudoklin","cba"])
        self.assertEqual(result, PathStatus.stop)   
        result= conf1.paths.GetPathStatus(["root","jaka","micka","cde"])
        self.assertEqual(result, PathStatus.stop)
        
        conf2= self.cmd.NewConfig("test2", "include", "test")
        conf2.paths.SetPathStatus(["root","jaka"], PathStatus.ignore)
        conf2.paths.SetPathStatus(["root","jaka","|hudoklin/micka/cba|cde|","jure"], PathStatus.stop)
        result= conf2.paths.GetPathStatus(["root","jaka", "hudoklin","micka","cde","jure"])
        self.assertEqual(result, PathStatus.stop)
        conf2.paths.SetPathStatus(["root","jaka","|\w+\.txt|"], PathStatus.include)
        result= conf2.paths.GetPathStatus(["root","jaka","test","file.txt"])
        self.assertEqual(result, PathStatus.include)
        result= conf2.paths.GetPathStatus(["root","jaka","file.txt"])
        self.assertEqual(result, PathStatus.include)
        result= conf2.paths.GetPathStatus(["root","jaka","file.mfd"])
        self.assertEqual(result, PathStatus.ignore)
        
        print self.cmd.GenConfigTree(True)  
        
        self.cmd.DelConfig("test")
        self.cmd.DelConfig("test2")
        
if __name__ == '__main__':
    unittest.main()