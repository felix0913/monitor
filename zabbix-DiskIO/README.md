## 使用说明

来自如下地址，稍作修改。    
> http://www.jianshu.com/p/62c86a397b4d

### 文件说明：

**zabbix_io_stats.conf**：Zabbix Agent 端的 Key 配置文件，放在 `/etc/zabbix/zabbix_agentd.d/` 目录下。

**discover_disk.pl**：自动发现脚本，需放在 agent 服务器上，供 `zabbix_io_stats.conf` 配置文件里调用。 

**Template_Linux_Disk_IO_Stats.xml**：Zabbix 模板文件，在 Web 端导入即可。   

### zabbix Agent 配置

- 编辑 zabbix agent 配置文件，设置 Include 目录：
  ```
  Include=/etc/zabbix/zabbix_agentd.d/*.conf
  ```
  
- 将自动发现脚本放入 `/usr/local/zabbix/scripts/` 目录下，可能没有此目录需单独创建：

  ```
  $ sudo mkdir -pv /usr/local/zabbix/scripts/
  mkdir: created directory ‘/usr/local/zabbix’
  mkdir: created directory ‘/usr/local/zabbix/scripts/’
  $ cd /usr/local/zabbix/scripts/
  scripts/$ sudo vim discover_disk.pl
  #!/usr/bin/perl

  sub get_vmname_by_id
    {
    $vmname=`cat /etc/qemu-server/$_[0].conf | grep name | cut -d \: -f 2`;
    $vmname =~ s/^\s+//; #remove leading spaces
    $vmname =~ s/\s+$//; #remove trailing spaces
    return $vmname
    }

  $first = 1;
  print "{\n";
  print "\t\"data\":[\n\n";

  for (`cat /proc/diskstats`)
    {
    ($major,$minor,$disk) = m/^\s*([0-9]+)\s+([0-9]+)\s+(\S+)\s.*$/;
    $dmnamefile = "/sys/dev/block/$major:$minor/dm/name";
    $vmid= "";
    $vmname = "";
    $dmname = $disk;
    $diskdev = "/dev/$disk";
    # DM name
    if (-e $dmnamefile) {
      $dmname = `cat $dmnamefile`;
      $dmname =~ s/\n$//; #remove trailing \n
      $diskdev = "/dev/mapper/$dmname";
      # VM name and ID
      if ($dmname =~ m/^.*--([0-9]+)--.*$/) {
        $vmid = $1;
        #$vmname = get_vmname_by_id($vmid);
        }
      }
    #print("$major $minor $disk $diskdev $dmname $vmid $vmname \n");

    print "\t,\n" if not $first;
    $first = 0;

    print "\t{\n";
    print "\t\t\"{#DISK}\":\"$disk\",\n";
    print "\t\t\"{#DISKDEV}\":\"$diskdev\",\n";
    print "\t\t\"{#DMNAME}\":\"$dmname\",\n";
    print "\t\t\"{#VMNAME}\":\"$vmname\",\n";
    print "\t\t\"{#VMID}\":\"$vmid\"\n";
    print "\t}\n";
    }

  print "\n\t]\n";
  print "}\n";

  增加可执行权限：
  scripts/$ sudo chmod a+x discover_disk.pl
  ```
  
- 将 `zabbix_io_stats.conf` Key 配置文件放入 `Include=/etc/zabbix/zabbix_agentd.d/` 目录下：

  ```
  $ cd /etc/zabbix/zabbix_agentd.d/
  zabbix_agentd.d$ sudo vim zabbix_io_stats.conf
  # diskio discovery
  UserParameter=discovery.disks.iostats,/usr/local/zabbix/scripts/discover_disk.pl
  #读扇区的次数
  UserParameter=custom.vfs.dev.read.sectors[*],cat /proc/diskstats | grep $1 | head -1 | awk '{print $$6}'
  #写扇区次数
  UserParameter=custom.vfs.dev.write.sectors[*],cat /proc/diskstats | grep $1 | head -1 | awk '{print $$10}'
  #合并读完成次数
  UserParameter=custom.vfs.dev.read.ops[*],cat /proc/diskstats | grep $1 | head -1 |awk '{print $$4}'
  #合并写完成次数
  UserParameter=custom.vfs.dev.write.ops[*],cat /proc/diskstats | grep $1 | head -1 | awk '{print $$8}'
  #读花费的毫秒数
  UserParameter=custom.vfs.dev.read.ms[*],cat /proc/diskstats | grep $1 | head -1 | awk '{print $$7}'
  #写操作花费的毫秒数
  UserParameter=custom.vfs.dev.write.ms[*],cat /proc/diskstats | grep $1 | head -1 | awk '{print $$11}'
  
  重启 zabbix 客户端服务：
  $ sudo service zabbix-agent restart
  ```
  
### 测试 Zabbix Agent 端是否设置成功

在 Zabbix Server 端使用 `zabbix_get -s Agent_IP -p 10050 -k Key_Value` 命令测试是否返回相关的信息。

```
  获取 discovery.disks.iostats 的值，是一个 JSON 格式的信息：
  $ zabbix_get -s 192.168.0.234 -p 10050 -k discovery.disks.iostats
  {
    "data":[

    {
      "{#DISK}":"ram0",
      "{#DISKDEV}":"/dev/ram0",
      "{#DMNAME}":"ram0",
      "{#VMNAME}":"",
      "{#VMID}":""
    }
    ,
    {
      "{#DISK}":"ram1",
      "{#DISKDEV}":"/dev/ram1",
      "{#DMNAME}":"ram1",
      "{#VMNAME}":"",
      "{#VMID}":""
    }
    .
    .
    .
    ]
  }
```


### Zabbix Web 配置

- 导入 Template_Linux_Disk_IO_Stats.xml 模板
  
  配置 -> 模板 -> 导入 -> 选择文件 -> 导入

- 增加新的正则表达式：

  管理 -> 一般 -> 正则表达式 -> 新的正则表达式
  
  正则表达式内容根据自己主机硬盘名称填写，类型为结果为真：
  
  ```
  #Linux disks for autodiscovery
  ^(xvda|xvdb|xvdc|sda|sdb|sdc)$
  ```
  
  ![](http://upload-images.jianshu.io/upload_images/3246264-ed8e5f19730d6219.gif?imageMogr2/auto-orient/strip%7CimageView2/2/w/700)
  
- 将模板应用到相关主机后等待片刻即可查看到监控的图信息：

  ![](http://upload-images.jianshu.io/upload_images/3246264-0d020895560c9601.png?imageMogr2/auto-orient/strip%7CimageView2/2/w/700)



