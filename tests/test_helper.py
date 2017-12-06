import os
import unittest

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

    @unittest.skipUnless(os.path.exists('/proc/1/cgroup'), 'Not running in a container')
    def test_container_id(self):
        self.assertIsNotNone(helper.get_current_container_id())
        
        for digit in helper.get_current_container_id():
            self.assertIn(digit, 'abcdefghijlkmnopqrstuvwxyz0123456789')

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

