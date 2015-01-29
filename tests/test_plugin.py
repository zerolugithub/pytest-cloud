"""Tests for pytest-bdd-splinter subplugin."""
import os.path
import sys

import mock
import pytest

PYTHON = 'python{0}.{1}'.format(*sys.version_info)


@pytest.mark.parametrize(
    ['host1', 'user1', 'cpu_count1', 'memory1', 'host2', 'user2', 'cpu_count2', 'memory2',
     'mem_per_process', 'max_processes', 'result'],
    [
        ('1.example.com', '', 2, 100,
         '2.example.com', 'user', 1, 200,
         None,
         None,
         [
             '1*ssh=1.example.com//id=1.example.com_0//chdir=test//python={0}'.format(PYTHON),
             '1*ssh=1.example.com//id=1.example.com_1//chdir=test//python={0}'.format(PYTHON),
             '1*ssh=user@2.example.com//id=2.example.com_0//chdir=test//python={0}'.format(PYTHON),
         ]),
        ('1.example.com', '', 2, 100,
         '2.example.com', 'user', 1, 200,
         200,
         None,
         [
             '1*ssh=user@2.example.com//id=2.example.com_0//chdir=test//python={0}'.format(PYTHON),
         ]),
        ('1.example.com', '', 2, 100,
         '2.example.com', 'user', 1, 200,
         None,
         1,
         [
             '1*ssh=1.example.com//id=1.example.com_0//chdir=test//python={0}'.format(PYTHON),
             '1*ssh=user@2.example.com//id=2.example.com_0//chdir=test//python={0}'.format(PYTHON),
         ]),
        ('1.example.com', '', 2, 100,
         '2.example.com', 'user', 1, 200,
         200,
         1,
         [
             '1*ssh=user@2.example.com//id=2.example.com_0//chdir=test//python={0}'.format(PYTHON),
         ]),
    ]
)
@mock.patch('xdist.dsession.DSession')
@mock.patch('execnet.Group')
@mock.patch('pytest_cloud.plugin.HostRSync')
def test_schedule(
        mocked_rsync, mocked_group, mocked_dsession, testdir, host1, host2, user1, user2, cpu_count1,
        cpu_count2, memory1, memory2, mem_per_process, max_processes, result):
    """Test scheduling of tests on given nodes."""
    ch1 = mock.Mock()
    ch1.gateway.id = host1
    ch2 = mock.Mock()
    ch2.gateway.id = host2
    mocked_group.mkgateway.return_value = mock.Mock()

    node1 = user1 + '@' + host1 if user1 else host1
    node2 = user2 + '@' + host2 if user2 else host2

    mocked_group.return_value.remote_exec.return_value.receive_each.return_value = [
        (ch1, {'cpu_count': cpu_count1, 'virtual_memory': {'free': memory1 * 1024 ** 2}}),
        (ch2, {'cpu_count': cpu_count2, 'virtual_memory': {'free': memory2 * 1024 ** 2}}),
    ]
    params = [
        '--cloud-nodes={0}'.format(node1), '--cloud-node={0}'.format(node2),
        '--cloud-chdir=test']
    if mem_per_process:
        params.append('--cloud-mem-per-process={0}'.format(mem_per_process))
    if max_processes:
        params.append('--cloud-max-processes={0}'.format(max_processes))
    testdir.inline_run(*params)
    assert mocked_rsync.call_args[0] == (os.path.dirname(os.path.dirname(sys.executable)),)
    assert mocked_rsync.return_value.add_target_host.call_args_list == [
        mock.call(mocked_group.return_value.makegateway.return_value,),
        mock.call(mocked_group.return_value.makegateway.return_value,)]
    assert mocked_rsync.return_value.send.called
    config = mocked_dsession.call_args[0][0]
    assert config.option.tx == result
    assert config.option.dist == 'load'
