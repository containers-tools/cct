import unittest
import mock
import six

from cct.modules.amq.cct_module import AMQ
from cct.errors import CCTError


class TestAMQModule:

    class TestAuthentication(unittest.TestCase):

        def setUp(self):
            self.amq = AMQ('amq', 'amq')

        @mock.patch('cct.modules.amq.cct_module.add_element')
        def test_should_setup_authentication(self, mock_add_element):
            m = mock.mock_open()
            with mock.patch.object(six.moves.builtins, 'open', m, create=True):
                self.amq.setup_authentication('user', 'pass')

            m.assert_called_once_with('users.ini', 'w')
            m().write.assert_called_once_with('user=pass\n')
            mock_add_element.assert_called_once_with(
                'activemq.xml', ".//*[local-name()='broker']/*[local-name()='plugins']", '<jaasAuthenticationPlugin configuration="activemq"/>')

        def test_should_fail_setup_authentication_when_there_is_no_password(self):
            with self.assertRaises(CCTError) as cm:
                self.amq.setup_authentication('user', None)

            self.assertEquals(str(
                cm.exception), 'Username or password not provided, we cannot proceed with setting up AMQ authentication without it')

        def test_should_fail_setup_authentication_if_empty_password_is_provided(self):
            with self.assertRaises(CCTError) as cm:
                self.amq.setup_authentication('user', '')
            self.assertEquals(str(
                cm.exception), 'Username or password not provided, we cannot proceed with setting up AMQ authentication without it')

    class TestTopicAndQueue(unittest.TestCase):

        def setUp(self):
            self.amq = AMQ('amq', 'amq')

        def test_should_raise_if_topic_name_is_not_provided(self):
            with self.assertRaises(CCTError) as cm:
                self.amq.define_topic('')

            self.assertEquals(str(
                cm.exception), 'No topic names provided, we cannot proceed with setting up AMQ topics without it')

        @mock.patch('cct.modules.amq.cct_module.add_element')
        @mock.patch('cct.modules.amq.cct_module.does_element_exists', side_effect=[True, False])
        def test_should_add_single_topic(self, mock_element_exists, mock_add_element):
            self.amq.define_topic('topicname')
            self.assertEqual(mock_add_element.call_count, 1)
            self.assertEqual(mock_add_element.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']", '<topic physicalName="topicname"/>'))
            self.assertEqual(mock_element_exists.call_count, 2)
            self.assertEqual(mock_element_exists.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']"))
            self.assertEqual(mock_element_exists.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='topicname']"))

        @mock.patch('cct.modules.amq.cct_module.add_element')
        @mock.patch('cct.modules.amq.cct_module.does_element_exists', side_effect=[True, False, False])
        def test_should_add_multiple_topic(self, mock_element_exists, mock_add_element):
            self.amq.define_topic('topic1,topic2')
            self.assertEqual(mock_add_element.call_count, 2)
            self.assertEqual(mock_add_element.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']", '<topic physicalName="topic1"/>'))
            self.assertEqual(mock_add_element.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']", '<topic physicalName="topic2"/>'))
            self.assertEqual(mock_element_exists.call_count, 3)
            self.assertEqual(mock_element_exists.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']"))
            self.assertEqual(mock_element_exists.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='topic1']"))
            self.assertEqual(mock_element_exists.mock_calls[2], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='topic2']"))

        @mock.patch('cct.modules.amq.cct_module.add_element')
        @mock.patch('cct.modules.amq.cct_module.does_element_exists', side_effect=[False, False])
        def test_should_add_single_topic_when_destinations_element_is_present(self, mock_element_exists, mock_add_element):
            self.amq.define_topic('topicname')
            self.assertEqual(mock_add_element.call_count, 2)
            self.assertEqual(mock_add_element.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='broker']", '<destinations></destinations>'))
            self.assertEqual(mock_add_element.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']", '<topic physicalName="topicname"/>'))
            self.assertEqual(mock_element_exists.call_count, 2)
            self.assertEqual(mock_element_exists.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']"))
            self.assertEqual(mock_element_exists.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='topicname']"))

        @mock.patch('cct.modules.amq.cct_module.add_element')
        @mock.patch('cct.modules.amq.cct_module.does_element_exists', side_effect=[True, True])
        def test_should_not_add_topic_when_it_already_exists(self, mock_element_exists, mock_add_element):
            self.amq.define_topic('topicname')
            self.assertEqual(mock_add_element.call_count, 0)
            self.assertEqual(mock_element_exists.call_count, 2)
            self.assertEqual(mock_element_exists.mock_calls[0], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']"))
            self.assertEqual(mock_element_exists.mock_calls[1], mock.call(
                'activemq.xml', ".//*[local-name()='destinations']/*[local-name()='topic' and @physicalName='topicname']"))

if __name__ == '__main__':
    unittest.main()
