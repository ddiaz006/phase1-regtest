#!/usr/bin/env python

import driver
import datetime, optparse, os, pickle, sys, time


def check_target(target):
    coords = target.split("-")
    fail = "Expected RBX-RM.  Found %s" % str(target)

    if len(coords) != 2:
        sys.exit(fail)

    rbx, rm_s = coords

    if not (rbx.startswith("HB") or rbx.startswith("HE")):
        sys.exit("This script only works with HB or HE RBXes.")

    try:
        rm = int(rm_s)
    except ValueError:
        sys.exit("Could not convert '%s' to an int." % rm_s)

    return target, rbx


def opts(multi_target=False):
    parser = optparse.OptionParser(usage="usage: %prog [options] RBX-RM")
    parser.add_option("--nseconds",
                      dest="nSeconds",
                      default=1,
                      type="int",
                      help="number of seconds to wait at each setting [default %default]")
    parser.add_option("--minimum",
                      dest="bvMin",
                      default=1,
                      type="int",
                      help="minimum BV setting (V) [default %default]")
    parser.add_option("--maximum",
                      dest="bvMax",
                      default=17,
                      type="int",
                      help="maximum BV setting (V) [default %default]")
    parser.add_option("--step",
                      dest="bvStep",
                      default=1,
                      type="int",
                      help="step size (V) [default %default]")
    parser.add_option("--default-server",
                      dest="defaultServer",
                      default=False,
                      action="store_true",
                      help="connect to default server in driver.py")

    options, args = parser.parse_args()

    if len(args) != 1 and not multi_target:
        parser.print_help()
        sys.exit(" ")

    return options, args


class scanner(driver.driver):
    def __init__(self, options, args):
        self.target, self.rbx = check_target(args[0])

        self.options = options
        self.options.logfile = self.target + ".log"

        self.assign_sector_host_port(default=self.options.defaultServer)
        self.connect()
        self.pickle(self.bv_scan())
        self.disconnect()


    def split_results(self, cmd):
        res = self.command(cmd)
        fields = res.split("#")
        #print(fields) 
        if " " in fields[1]:
            res1 = fields[1].split()
        elif type(fields[1]) is not list:
            res1 = [fields[1]]

        if res1 == ["OK"]:
            results = res1
        elif res1[0].strip().startswith("0x"):
            results = [int(x, 16) for x in res1]
        else:
            results = [float(x) for x in res1]
        return fields[0], results


    def bv_scan(self):
        nCh = 48 if self.he else 64

                     #"PeltierVoltage" in cmd:
        #filename = "%s_%s.txt" % (self.target, datetime.datetime.today().strftime("%Y_%m_%d_%Hh%M"))
        filename = open("test.txt", "w")
        d = {}
        p = {}
        #print >>filename,BVIn  
        for w in range(self.options.bvMin, self.options.bvMax + self.options.bvStep, self.options.bvStep):
            v=(w/2.0) -1.0
            #print("This Is V:  " + str(v))
	    if v < 0:
            	BVIn="get %s-BVin_f_rr" % (self.target)
            	p[(v, BVIn)] = self.split_results(BVIn)[1]
                out= "BV_In:" + str(self.split_results(BVIn)[1])
                #print ("TEST    "+out+"        ENDTEST\n")
		print >>filename, out 
		print >>filename, "#SetV I_Pel V_Pel MonV_Pel" 
            else :
                out3=" "
                "put %s-biasvoltage[1-%d]_f %d*%f" % (self.target, nCh, nCh, v)
                SetVPel="put %s-SetPeltierVoltage_f %f" % (self.target, v)
                SetVPel_1= " " + str(self.split_results(SetVPel)[1])

                MonVPel="get %s-PeltierVoltageMon_f_rr" % (self.target)
                MonVPel_1= " " + str(self.split_results(MonVPel)[1])
                
                time.sleep(1*self.options.nSeconds)
                VPel="get %s-PeltierVoltage_f_rr" % (self.target)
                VPel_1= " " + str(self.split_results(VPel)[1])
                IPel="get %s-PeltierCurrent_f_rr" % (self.target)
                IPel_1= " " + str(self.split_results(IPel)[1])
            	#d[(v, VPel)] = self.split_results(VPel)[0]
            	#d[(v, MonVPel)] = self.split_results(MonVPel)[0]
            	#d[(v, IPel)] = self.split_results(IPel)[0]
           	#for cmd in ["get %s-PeltierVoltageMon_f_rr" % (self.target),
           	#            "get %s-PeltierCurrent_f_rr" % (self.target),
           	#            "get %s-PeltierVoltage_f_rr" % (self.target)
           	#            ]:
                #   if "PeltierCurrent" in cmd:
                #     time.sleep(2*self.options.nSeconds)
                #   #if "PeltierCurrent" in cmd:
                #   #  IPel=str(self.split_results(cmd)[1]
                #   #if "PeltierVoltage" in cmd:
                #   #   print("in inner loop") 
                #   #  if "Mon" in cmd:
                #   #     MonVPel=str(self.split_results(cmd)[1]
                #   #  else :
                #   #     VPel=str(self.split_results(cmd)[1]
                #   d[(v, cmd)] = self.split_results(cmd)[1]
                #print("put HB1-2-SetPeltierVoltage_f   " + str(v))
                out3=str(v)+" "+str(IPel_1)+str(VPel_1)+str(MonVPel_1)
                #print (out3)
                #   out2= str(v)+" "+str(self.split_results(cmd)[0]) + str(self.split_results(cmd)[1])
                #   out= str(v)+" " + str(self.split_results(cmd)[0]) + str(self.split_results(cmd)[1])
                #   print ("TEST    "+out+"        ENDTEST\n")
                print >>filename, out3 
                raw_input("put HB1-2-SetPeltierVoltage_f   " + str(v)+ ",     Press Enter to continue...")
        #print("Wrote results to %s" % filename)
        filename.close()
        return d



    def pickle(self, d):
        filename = "%s_%s.pickle" % (self.target, datetime.datetime.today().strftime("%Y_%m_%d_%Hh%M"))
        with open(filename, "w") as f:
            pickle.dump(d, f)
        #print("Wrote results to %s" % filename)


if __name__ == "__main__":
    p = scanner(*opts())
