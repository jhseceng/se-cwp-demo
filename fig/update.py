##python3.7
##Dixon Styres 1/9/19
##Work@Crowdstrike

#update.py will run and install updates for the FIG

import os
import shutil
import glob

class Update():
    def __init__(self):
        self.cwd = os.getcwd()
        self.fig = '/home/ec2-user/AWS-SecurityHub-Provider/src/'
        self.files = (glob.glob("%s/*.py"%self.cwd))
        for file in self.files:
            if("update.py" in file):
                continue
            self.copy(file,self.fig)

    def copy(self, src, dest):
        try:
            shutil.copy(src, dest)
            print("Copying %s to %s" %(src,dest))
        except:
            print("Error Copying %s to %s" %(src,dest))
Update()
