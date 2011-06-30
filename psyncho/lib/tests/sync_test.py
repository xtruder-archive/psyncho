import unittest
import pat  # touch pat.py in the cwd and try to import the empty file under Linux
import string 

from command import PsynchoCommand
from psyncho import *
from fs.opener import fsopendir

class TestSynch(unittest.TestCase): 
    @classmethod
    def setUpClass(cls):
        cls.cmd= PsynchoCommand()
        
    def Makedirs(self, path, root, dirs):
        f= fsopendir(path)
        for dir in dirs:
            f.makeopendir(root+"/"+dir, recursive=True)
            
    def Deldirs(self, path, root, dirs):
        f= fsopendir(path)
        for dir in dirs:
            try:
                f.removedir(root+"/"+dir, recursive=True, force=True)
            except:
                continue
            
    def Checkdirs(self, path, root, dirs, correct_dirs):
        f= fsopendir(path)
        for dir in dirs:
            if f.isdir(root+"/"+dir):
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
        dirs1=["a/m/file","b/c/file","c"]
        self.Makedirs(self.CurrentDir()+"/testdirs","test1",dirs1)
        self.Makedirs(self.CurrentDir()+"/testdirs","test2",[""])
        self.cmd.NewConfig("test", "include", None)
        self.cmd.SelectCurrentConfig("test")
        self.cmd.SetPathStatus("root/a", "ignore")
        self.cmd.SetPathStatus("root/b", "include")
        self.cmd.SetPathStatus("root/c", "stop")
        self.cmd.NewConfig("test2", "include", "test")
        self.cmd.SelectCurrentConfig("test2")
        self.cmd.SetPathStatus("root/a/m/file", "include")
        self.cmd.SetPathStatus("root/a/file", "include")
        self.cmd.SetPathStatus("root/b/c/file", "stop")
        
        self.cmd.NewSynch("synchtest1","./testdirs/test1", "./testdirs/test2", "test2")
        self.cmd.Synch("synchtest1")
        
        correct_dirs=["a/m/file","b"]
        self.Checkdirs(self.CurrentDir()+"/testdirs","test1",dirs1,correct_dirs)
        self.Checkdirs(self.CurrentDir()+"/testdirs","test2",dirs1,correct_dirs)
        
        self.Deldirs(self.CurrentDir()+"/testdirs","test1",[""])
        self.Deldirs(self.CurrentDir()+"/testdirs","test2",[""])
        
        self.cmd.DelConfig("test")
        self.cmd.DelConfig("test2")
        
if __name__ == '__main__':
    unittest.main()