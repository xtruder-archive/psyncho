import unittest
import pod

from psyncho import *

class TestConfigLayer(unittest.TestCase): 
    def RecursiveLen(self, obj):
        count= 0
        for a in obj:
            count+=1
            
        return count
    
    @classmethod
    def setUpClass(cls):
        cls.db = pod.Db(file = 'UnisonConfig.db', dynamic_index = True) 
        
    def test_synch(self):
        config= ConfigLayer("test1", None, PathStatus.include )
        fsconfig= FileSyncConfig("/home/offlinehacker/test1", "/home/offlinehacker/test2", config)
        f= FileSync(fsconfig)
        f.sync()  
           
    def test_GettingPathStatus(self):
        for mgr in ConfigLayerManager:
            mgr.delete()
            
        for conf in ConfigLayer:
            conf.delete()
            
        for path in PathPart:
            path.delete()
            
        self.db.commit()

        layer1=ConfigLayer("test3", None, PathStatus.include, None)
        layer1.paths.SetPathStatus(["root","jaka"], PathStatus.include)    
        layer2=ConfigLayer("test2", None, PathStatus.include, layer1)
        layer2.paths.SetPathStatus(["root","jaka","hudoklin"], PathStatus.include)
        layer2.paths.SetPathStatus(["root","jaka","hudoklin","cba"], PathStatus.stop)
        layer3=ConfigLayer("test", None, PathStatus.include, layer2)
        layer3.paths.SetPathStatus(["root","jaka","hudoklin","cba","status"], PathStatus.include)
        
        mgr= ConfigLayerManager()
        mgr.AddConfig(layer1)
        
        status= layer3.GetPathStatus(["root","jaka","hudoklin","cba","status"])
        self.assertEqual(status, PathStatus.stop)
        
        mgr.RemoveConfig(layer1)
        
        self.assertEqual(len(mgr.configs),0)
        
        self.db.commit()
        
        self.assertEqual(self.RecursiveLen(ConfigLayerManager), 1)
        self.assertEqual(self.RecursiveLen(ConfigLayer), 0)
        self.assertEqual(self.RecursiveLen(PathPart), 0) 
        
if __name__ == '__main__':
    unittest.main()