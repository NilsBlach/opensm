#!/usr/bin/env python

from sys import argv, exit, stdout
from subprocess import Popen, PIPE
from os import path, kill
from signal import SIGUSR2
from re import compile
from argparse import ArgumentParser
from contextlib import contextmanager
from csv import reader as csv_reader
from csv import writer as csv_writer

@contextmanager
def __smart_open(filename=None):
    if filename and filename != '-':
        fh = open(filename, 'w')
    else:
        fh = stdout
    try:
        yield fh
    finally:
        if fh is not stdout:
            fh.close()


def _convert_comm_demand_and_hostlist_to_csv(demand_file, host_file, out_csv_file):
    srcdst = {}
    with open(demand_file, 'r') as demand_csv:
        demand_matrix_reader = csv_reader(demand_csv, delimiter=',')
        src_mpi_rank = 0
        max_weight = 0
        for row in demand_matrix_reader:
            dst_mpi_rank = 0
            srcdst[src_mpi_rank] = {}
            for demand in row:
                weight = int(demand)
                srcdst[src_mpi_rank][dst_mpi_rank] = weight
                if weight > max_weight:
                    max_weight = weight
                dst_mpi_rank += 1
            src_mpi_rank += 1

        # down scale weights to be \in [1, 255]
        if max_weight > 255:
            for src_rank in srcdst:
                for dst_rank in srcdst[src_rank]:
                    if 0 == srcdst[src_rank][dst_rank]: continue
                    new_weight = int(srcdst[src_rank][dst_rank] * 255.0 / max_weight)
                    if new_weight < 1:
                        new_weight = 1
                    srcdst[src_rank][dst_rank] = new_weight
    #print(srcdst)

    hosts = {}
    host_name = compile('^\s*(\w+)')
    with open(host_file, 'r') as hostlist:
        hostID = 0
        for line in hostlist:
            if host_name.match(line):
                hosts[hostID] = host_name.match(line).group(1)
                hostID += 1
    #print(hosts)

    with __smart_open(out_csv_file) as out_csv:
        out_csv_writer = csv_writer(out_csv, delimiter=',')
        for src_rank in srcdst:
            src_host = hosts[src_rank]
            row = [src_host, len([dst_rank for dst_rank in srcdst[src_rank] if srcdst[src_rank][dst_rank] > 0])]
            for dst_rank in sorted(srcdst[src_rank].keys()):
                if 0 == srcdst[src_rank][dst_rank]: continue
                row += [hosts[dst_rank], srcdst[src_rank][dst_rank]]
            # need the entry even if len(row)=2 otherwise parx gets confused
            out_csv_writer.writerow(row)


def _convert_comm_demands_and_hostlists_to_csv_for_osm(args):
    if not isinstance(args, dict):
        exit('ERR: invalid function parameter type(s)')

    with __smart_open(path.join(args.get('__csv_output_dir__'), args.get('__output__'))) as out:
        for jobID in range(len(args.get('__comm_demand_files__'))):
            demand_file = args.get('__comm_demand_files__')[jobID]
            host_file = args.get('__host_files__')[jobID]
            _convert_comm_demand_and_hostlist_to_csv(
                    path.join(args.get('__comm_demands_dir__'), demand_file),
                    path.join(args.get('__host_files_dir__'), host_file),
                    path.join(args.get('__csv_output_dir__'), 'job%s.csv' % str(jobID).zfill(4)))
            out.write('%s\n' % path.join(args.get('__csv_output_dir__'), 'job%s.csv' % str(jobID).zfill(4)))


def _signal_osm_to_reroute_fabric(args):
    if not isinstance(args, dict):
        exit('ERR: invalid function parameter type(s)')

    if args.get('__trigger_rerouting__'):
        try:
            osm_pid = Popen(
                [path.join('/',
                           'sbin',
                           'pidof'),
                 'opensm'],
                stdout=PIPE,
                stderr=PIPE).communicate()[0]
        except:
            exit('ERR: not able to get the pid of opensm')
        else:
            try:
                osm_pid = int(osm_pid)
            except:
                exit('ERR: no valid pid of opensm found')
            else:
                kill(osm_pid, SIGUSR2)


def _get_arg_parser():
    arg_parser = ArgumentParser()
    arg_parser.add_argument(
        '--comm_demands_dir',
        dest='__comm_demands_dir__',
        metavar='<DIR>',
        help='directory containing files with communication demands',
        required=True,
        default=None)
    arg_parser.add_argument(
        '--comm_demand_files',
        dest='__comm_demand_files__',
        nargs='+',
        metavar='<FILE>',
        help='files containing communication demands of jobs in 1-to-1 mapping with host_files',
        required=True,
        default=None)
    arg_parser.add_argument(
        '--host_files_dir',
        dest='__host_files_dir__',
        metavar='<DIR>',
        help='directory containing host files for mpi jobs',
        required=True,
        default=None)
    arg_parser.add_argument(
        '--host_files',
        dest='__host_files__',
        nargs='+',
        metavar='<FILE>',
        help='files with nodes lists per job in 1-to-1 mapping with comm_demand_files',
        required=True,
        default=None)
    arg_parser.add_argument(
        '--csv_output_dir',
        dest='__csv_output_dir__',
        metavar='<DIR>',
        help='directory to store the processed communication demands',
        required=True,
        default=None)
    arg_parser.add_argument(
        '--output',
        dest='__output__',
        metavar='<FILE>',
        help='file containing list of file(s) with comm. demand matrix for osm to read; written into csv_output_dir',
        default=None)
    arg_parser.add_argument(
        '--trigger_osm',
        dest='__trigger_rerouting__',
        help='send signal to OpenSM/parx routing to reroute fabric optimized for communication demands',
        action='store_true',
        default=False)

    args = vars(arg_parser.parse_args())

    if len(args.get('__comm_demand_files__')) != len(args.get('__host_files__')):
        exit('ERR: input mismatch; need equ. number of comm_demand_files and host_files')

    if not path.isdir(args.get('__comm_demands_dir__')):
        exit('ERR: %s not a valid directory' % args.get('__comm_demands_dir__'))

    for f in args.get('__comm_demand_files__'):
        if not path.join(args.get('__comm_demands_dir__'), f):
            exit('ERR: %s not found' % path.join(args.get('__comm_demands_dir__'), f))

    if not path.isdir(args.get('__host_files_dir__')):
        exit('ERR: %s not a valid directory' % args.get('__host_files_dir__'))

    for f in args.get('__host_files__'):
        if not path.join(args.get('__host_files_dir__'), f):
            exit('ERR: %s not found' % path.join(args.get('__host_files_dir__'), f))

    if not path.isdir(args.get('__csv_output_dir__')):
        exit('ERR: %s not a valid directory' % args.get('__csv_output_dir__'))

    return args


if __name__ == '__main__':
    args = _get_arg_parser()
    _convert_comm_demands_and_hostlists_to_csv_for_osm(args)
    _signal_osm_to_reroute_fabric(args)
