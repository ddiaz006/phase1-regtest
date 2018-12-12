#!/usr/bin/env python2

import ngfec, printer
import collections, datetime, sys, time


class driver:
    def __init__(self, options, target):
        self.options = options
        self.rbx = target
        self.target = target

        self.connect()
        self.bail()


    def enable(self):
        pass


    def errors(self, store=True):
        msg = "Reading link error counters"
        if store:
            msg += " (integrating for %d seconds)" % self.options.nSeconds

        if hasattr(self, "target0"):
            target0 = self.target0
        else:
            target0 = self.rbx

        print(msg)
        fec = "get %s-fec_[rx_prbs_error,dv_down]_cnt_rr" % target0
        ccm = "get %s-mezz_rx_[prbs,rsdec]_error_cnt_rr" % target0
        b2b = "get %s-[,s]b2b_rx_[prbs,rsdec]_error_cnt_rr" % target0

        if store:
            self.fec1 = self.command(fec)
            self.ccm1 = self.command(ccm)
            self.b2b1 = self.command(b2b)
            time.sleep(self.options.nSeconds)

        fec2 = self.command(fec)
        ccm2 = self.command(ccm)
        b2b2 = self.command(b2b)

        minimal = not store

        if self.fec1 != fec2:
            self.bail(["Link errors detected via FEC counters:", self.fec1[0], fec2[0]], minimal=minimal, note="fec_ber")
        if self.ccm1 != ccm2:
            self.bail(["Link errors detected via CCM counters:", self.ccm1[0], ccm2[0]], minimal=minimal, note="ccm_ber")
        if self.b2b1 != b2b2:
            lines = ["Link errors detected via CCM counters:", self.b2b1, b2b2]
            if store or (not self.target.endswith("neigh")):
                self.bail(lines, minimal=minimal, note="b2b_ber")
            else:  # don't exit due to b2b errors generated by using jtag/neigh
                printer.red("\n".join(lines))


    def ground0(self):
        if self.options.ground0:
            print("Ground stating")
            self.command("tput %s-lg go_offline" % self.rbx)
            self.command("tput %s-lg ground0" % self.rbx)
            self.command("tput %s-lg waitG" % self.rbx)
            self.command("tput %s-lg push" % self.rbx)


    def bail(self, lines=[], minimal=False, note="unspecified"):
        if lines:
            printer.purple("Exiting due to \"%s\"" % note)

        if not minimal:
            self.enable()
            self.errors(store=False)

        self.disconnect()

        if lines:
            raise RuntimeError(note, "\n".join(lines))


    def connect(self, quiet=False):
        self.logfile = open(self.options.logfile, "a")
        if not quiet:
            printer.gray("Appending to %s (consider doing \"tail -f %s\" in another shell)" % (self.options.logfile, self.options.logfile))
        h = "-" * 30 + "\n"
        self.logfile.write(h)
        self.logfile.write("| %s |\n" % str(datetime.datetime.today()))
        self.logfile.write(h)

        # ngfec.survey_clients()
        ngfec.kill_clients()
        self.server = ngfec.connect(self.options.host, self.options.port, self.logfile)


    def disconnect(self):
        ngfec.disconnect(self.server)
        self.logfile.close()


    def command(self, cmd):
        out = ngfec.command(self.server, cmd)[0]
        if "ERROR" in out:
            print(out)
        return out


def fake_options():
    out = collections.namedtuple('options', 'logfile host port nSeconds')
    out.logfile = "driver.log"
    out.host = "localhost"
    out.port = 54321
    out.nSeconds = 5
    return out


def main():
    try:
        driver(fake_options(), "target")
    except RuntimeError as e:
        printer.red(e[1])
        sys.exit(" ")


if __name__ == "__main__":
    main()
