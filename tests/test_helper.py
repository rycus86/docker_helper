import os
import unittest
import tempfile

import docker_helper as helper


class DockerHelperTest(unittest.TestCase):
    def setUp(self):
        secret_content = """
        KEY_A=aaa
        KEY_B=bbb
        """

        config_content = """
        CONF_A=config-A
        CONF_B=config=B
        """

        with open('/tmp/docker_helper_test_secret', 'w') as secret:
            for line in secret_content.splitlines():
                if line.strip():
                    secret.write(line.strip())
                    secret.write('\n')

        with open('/tmp/docker_helper_test_config_multi', 'w') as config:
            for line in config_content.splitlines():
                if line.strip():
                    config.write(line.strip())
                    config.write('\n')
        
        with open('/tmp/docker_helper_test_config', 'w') as config:
            config.write('Sample\nconfiguration')

    def tearDown(self):
        os.remove('/tmp/docker_helper_test_secret')
        os.remove('/tmp/docker_helper_test_config')
        os.remove('/tmp/docker_helper_test_config_multi')

    @unittest.skipUnless(os.path.exists('/proc/self/cgroup'), 'Not running in a container')
    def test_container_id(self):
        self.assertIsNotNone(helper.get_current_container_id())
        
        for digit in helper.get_current_container_id():
            self.assertIn(digit, 'abcdef0123456789')

    def test_mock_container_id(self):
        with tempfile.NamedTemporaryFile(mode='w') as tmp:
            tmp.write("""
10:perf_event:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
9:cpuset:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
8:pids:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
7:devices:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
6:net_cls,net_prio:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
5:blkio:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
4:freezer:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
3:memory:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
2:cpu,cpuacct:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
1:name=systemd:/docker/0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf
            """)
            tmp.flush()

            self.assertEqual(
                helper.get_current_container_id(read_from=tmp.name),
                '0aefd0c98f1af9b7fd5c09d576e5840ee9e798136b4a953b001587b1f0496adf'
            )

    def test_mock_container_id_with_cgroup_parent(self):
        with tempfile.NamedTemporaryFile(mode='w') as tmp:
            tmp.write("""
10:perf_event:/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
9:cpuset:/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
8:pids:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
7:devices:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
6:net_cls,net_prio:/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
5:blkio:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
4:freezer:/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
3:memory:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
2:cpu,cpuacct:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
1:name=systemd:/system.slice/docker.service/custom-cgroup/48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53
            """)
            tmp.flush()

            self.assertEqual(
                helper.get_current_container_id(read_from=tmp.name),
                '48b20f6cb5ea9d19407984994b312e85cfa4fce2fe5aac7d0b9e38ce86d9bd53'
            )

    def test_configuration(self):
        os.environ['CONF_B'] = 'env=value=B'
        os.environ['CONF_C'] = 'env=value=C'
        os.environ['TEST_ENV'] = 'testing'
        
        rc = helper.read_configuration

        self.assertEqual(rc('CONF_A', '/tmp/docker_helper_test_config_multi'), 'config-A')
        self.assertEqual(rc('CONF_B', '/tmp/docker_helper_test_config_multi'), 'config=B')
        self.assertEqual(rc('CONF_C', '/tmp/docker_helper_test_config_multi'), 'env=value=C')
        self.assertEqual(rc('CONF_C', '/tmp/docker_helper_test_config_multi', fallback_to_env=False), None)
        self.assertEqual(rc('CONF_C', '/tmp/docker_helper_test_config_multi', default='default', fallback_to_env=False), 'default')
        self.assertEqual(rc('CONF_D', default='x'), 'x')

        self.assertEqual(rc('KEY_A', '/tmp/docker_helper_test_secret', 'default'), 'aaa')
        self.assertEqual(rc('KEY_B', '/tmp/docker_helper_test_secret', 'default'), 'bbb')
        self.assertEqual(rc('KEY_C', '/tmp/docker_helper_test_secret', 'default'), 'default')

        self.assertEqual(rc('APP_CONFIG', '/tmp/docker_helper_test_config', single_config=True), 'Sample\nconfiguration')
        self.assertEqual(rc('TEST_ENV', 'non-existing', default='default', single_config=True), 'testing')

