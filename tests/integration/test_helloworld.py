import os
import subprocess
from pathlib import Path

import pytest
from pkg_resources import resource_filename

from jina.clients import py_client
from jina.clients.python.io import input_numpy
from jina.flow import Flow
from jina.helloworld import download_data
from jina.main.parser import set_hw_parser
from tests import JinaTestCase


class HelloWorldTestCase(JinaTestCase):

    @pytest.mark.timeout(360)
    def test_helloworld(self):
        subprocess.check_call(['jina', 'hello-world'])

    @pytest.mark.timeout(360)
    def test_helloworld_py(self):
        from jina.main.parser import set_hw_parser
        from jina.helloworld import hello_world
        hello_world(set_hw_parser().parse_args([]))

    @pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
    def test_helloworld_flow(self):
        args = set_hw_parser().parse_args([])

        os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
        os.environ['SHARDS'] = str(args.shards)
        os.environ['PARALLEL'] = str(args.parallel)
        os.environ['HW_WORKDIR'] = args.workdir
        os.environ['WITH_LOGSERVER'] = str(args.logserver)

        f = Flow.load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml'))))

        targets = {
            'index': {
                'url': args.index_data_url,
                'filename': os.path.join(args.workdir, 'index-original')
            },
            'query': {
                'url': args.query_data_url,
                'filename': os.path.join(args.workdir, 'query-original')
            }
        }

        # download the data
        Path(args.workdir).mkdir(parents=True, exist_ok=True)
        download_data(targets)

        # run it!
        with f:
            py_client(host=f.host,
                      port_expose=f.port_expose,
                      ).index(input_numpy(targets['index']['data']), batch_size=args.index_batch_size)

    def test_helloworld_flow_dry_run(self):
        args = set_hw_parser().parse_args([])

        os.environ['RESOURCE_DIR'] = resource_filename('jina', 'resources')
        os.environ['SHARDS'] = str(args.shards)
        os.environ['PARALLEL'] = str(args.parallel)
        os.environ['HW_WORKDIR'] = args.workdir
        os.environ['WITH_LOGSERVER'] = str(args.logserver)

        # run it!
        with Flow.load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.index.yml')))):
            pass

        # run it!
        with Flow.load_config(resource_filename('jina', '/'.join(('resources', 'helloworld.flow.query.yml')))):
            pass

    @pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
    @pytest.mark.skipif('HTTP_PROXY' not in os.environ, reason='skipped. '
                                                               'Set os env `HTTP_PROXY` if you want run test at your local env.')
    def test_download_proxy(self):
        import urllib.request
        # first test no proxy
        args = set_hw_parser().parse_args([])

        opener = urllib.request.build_opener()
        if args.download_proxy:
            proxy = urllib.request.ProxyHandler({'http': args.download_proxy, 'https': args.download_proxy})
            opener.add_handler(proxy)
        urllib.request.install_opener(opener)
        # head check
        req = urllib.request.Request(args.index_data_url, method="HEAD")
        response = urllib.request.urlopen(req, timeout=5)
        assert response.status == 200

        # test with proxy
        args = set_hw_parser().parse_args(["--download-proxy", os.getenv("HTTP_PROXY")])

        opener = urllib.request.build_opener()
        if args.download_proxy:
            proxy = urllib.request.ProxyHandler({'http': args.download_proxy, 'https': args.download_proxy})
            opener.add_handler(proxy)
        urllib.request.install_opener(opener)
        # head check
        req = urllib.request.Request(args.index_data_url, method="HEAD")
        response = urllib.request.urlopen(req, timeout=5)
        assert response.status == 200

