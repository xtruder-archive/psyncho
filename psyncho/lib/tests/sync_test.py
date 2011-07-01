import unittest
import pat  # touch pat.py in the cwd and try to import the empty file under Linux
import string 

from command import PsynchoCommand
from psyncho import *
from fs.opener import fsopendir
from copy import deepcopy

class TestSynch(unittest.TestCase): 
    @classmethod
    def setUpClass(cls):
        cls.cmd= PsynchoCommand()
        
    def OpenDirOrFile(self, f, root, dir):
            if dir.split("/")[-1:][0].count(".")>0:
                f.makeopendir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True)
                f.createfile(root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
            else:
                f.makeopendir(root+"/"+dir, recursive=True)
                
    def RemoveDirOrFile(self, f, root, dir):
            if dir.split("/")[-1:][0].count(".")>0:
                f.remove(root+"/"+"/".join(dir.split("/")[:-1])+"/"+dir.split("/")[-1:][0])
                f.removedir(root+"/"+"/".join(dir.split("/")[:-1]), recursive=True, force=True)
            else:
                f.removedir(root+"/"+dir, recursive=True, force=True)         
        
    def Makedirs(self, path, root, dirs):
        f= fsopendir(path)
        for dir in dirs:
            self.OpenDirOrFile(f, root, dir)
    def Deldirs(self, path, root, dirs):
        f= fsopendir(path)
        for dir in dirs:
            try:
                self.RemoveDirOrFile(f, root, dir)
            except:
                continue
            
    def Checkdirs(self, path, root, dirs, correct_dirs):
        f= fsopendir(path)
        for dir in dirs:
            if f.isdir(root+"/"+dir):
                self.assertTrue(dir in correct_dirs)
            elif f.isfile(root+"/"+dir):
                self.assertTrue(dir in correct_dirs)
            
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
        dirs1=["a/m/file.txt", "a/file.txt","b/c/file.txt","c"]
        self.Makedirs(self.CurrentDir()+"/testdirs","test1",dirs1)
        self.Makedirs(self.CurrentDir()+"/testdirs","test2",[""])
        self.cmd.NewConfig("test", "include", None)
        self.cmd.SelectCurrentConfig("test")
        self.cmd.SetPathStatus("root/a", "ignore")
        self.cmd.SetPathStatus("root/b", "include")
        self.cmd.SetPathStatus("root/c", "stop")
        self.cmd.NewConfig("test2", "include", "test")
        self.cmd.SelectCurrentConfig("test2")
        self.cmd.SetPathStatus("root/a/m/file.txt", "include")
        self.cmd.SetPathStatus("root/a/file.txt", "include")
        self.cmd.SetPathStatus("root/b/c/file.txt", "stop")
        
        self.cmd.NewConfig("test2", "include", "test->test2")
        
        self.cmd.NewSynch("synchtest1","./testdirs/test1", "./testdirs/test2", "test2")
        self.cmd.Synch("synchtest1")
        
        print self.cmd.GenConfigTree(True)     
        
        correct_dirs=["a/m/file.txt","b/c", "a/file.txt"]
        self.Checkdirs(self.CurrentDir()+"/testdirs","test1",dirs1,correct_dirs)
        self.Checkdirs(self.CurrentDir()+"/testdirs","test2",dirs1,correct_dirs)
        
        self.Deldirs(self.CurrentDir()+"/testdirs","test1",[""])
        self.Deldirs(self.CurrentDir()+"/testdirs","test2",[""])
        
        self.cmd.DelConfig("test")
        self.cmd.DelConfig("test2")
        
    def test_regex(self):
        conf1= self.cmd.NewConfig("test", "include", None)
        #First rule ovverides second
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
        
        self.cmd.DelConfig("test")
        
if __name__ == '__main__':
    unittest.main()