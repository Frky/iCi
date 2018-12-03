#-*- coding: utf-8 -*-

from datetime import datetime
import os
import shutil
import subprocess

class Pintool(object):

    def __init__(self, pin_path, pin_bin, flags, src_path, obj_path):
        self.__pin_path = pin_path
        self.__pin_bin = pin_bin
        self.__flags = flags
        self.__src_path = src_path
        self.__obj_path = obj_path

    def compile(self, analysis):
        """
            Compile the pintool

        """
        #TODO os independent

        src_path, src_name = os.path.split(self.__src_path)
        obj_path, obj_name = os.path.split(self.__obj_path)
        obj_path = os.path.abspath(obj_path)

        obj_build_path = "{}/build".format(obj_path)
        obj_build_name = src_name[:-4] + "-release"

        if not os.path.exists(obj_build_path):
            os.makedirs(obj_build_path)

        obj_build_file = "{}/{}.so".format(obj_build_path, obj_build_name)
        if os.path.exists(obj_build_file):
            mtime_before = os.stat(obj_build_file).st_mtime
        else:
            mtime_before = 0

        cmd = "make -B PIN_ROOT='{}' SCAT_COMPILE_FLAGS='{} {}' OBJDIR='{}/' '{}/{}.so'".format(
                self.__pin_path,
                self.__flags,
                " ".join(["-D{}".format(an.upper()) for an in analysis]),
                obj_build_path,
                obj_build_path,
                obj_build_name)
        with open("/dev/null", 'w') as fnull:
            try:
                subprocess.check_call(cmd, cwd=src_path, shell=True, stdout=fnull)
                mtime_now = os.stat("{}/{}.so".format(obj_build_path, obj_build_name)).st_mtime
                shutil.copyfile(
                        '{}/{}.so'.format(obj_build_path, obj_build_name),
                        '{}/{}'.format(obj_path, obj_name))
                # if mtime_before == mtime_now:
                #     # self.stdout("\t=> Up to date !", verbose=verbose)
                # else:
                #     # self.stdout("\t=> Done !", verbose)
                return True
            except subprocess.CalledProcessError as error:
                return False

    def launch(self, binary, args, infile, outdir, pin_args=None):
        """
            Launch the pintool analysis

            @param binary   the binary file to analyse (must be a valid path to
                            an executable)

            @param args     arguments to give to the binary

            @param verbose  if True, print intermediate steps

        """
        cmd = self.__cmd(binary, args, infile, outdir, pin_args)
        start = datetime.now()
        print cmd
        subprocess.call(cmd, shell=True)
        duration = datetime.now() - start

    def __cmd(self, binary, args, infile, outfile, pin_args):
        return "{} -ifeellucky -t {} {} -o {} -p {} {} -- {} {}".format(
                self.__pin_bin,
                self.__obj_path,
                "-i {}".format(infile) if infile else "",
                outfile,
                os.path.basename(binary),
                pin_args if pin_args else "",
                binary,
                args if args else "",
        )
