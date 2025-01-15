import dpkt
import pickle
import numpy as np

def analyse_algorithm(pcap_file_path,alg, cache=True):
    bucket_size=0.1 # in seconds
    pcap = dpkt.pcap.Reader(open(pcap_file_path, mode="rb"))
    bucket_start = -1
    buckets, bucket, jain = {}, {}, {}
    prev_bucket = []
    flows = {}

    for ts,buf in pcap:
        # 优先处理时间，将一个 bucket 中发生的事件做统计
        if bucket_start + bucket_size <= ts or bucket_start == -1:
            for x in bucket:
                bucket[x] /= ts - bucket_start
            if len(bucket) > 0:
                buckets[ts] = bucket
            tpts = [bucket[x] for x in bucket]
            if len(prev_bucket) != len(bucket):
                # Ignore these border cases for jain index as they may be inaccurate
                pass
            else:
                if tpts != []:
                    jain[ts] = sum(tpts) ** 2 / (len(tpts) * sum([x ** 2 for x in tpts]))
                else: jain[ts] = 0
            prev_bucket = bucket
            bucket_start = ts
            bucket = {}
        eth = dpkt.ethernet.Ethernet(buf)
        try:
           ip = dpkt.ip.IP(buf)
        except:
           continue
        eth.data = ip
        if type(eth.data) == str or	type(eth.data.data) == str:
            continue
        if type(eth.data.data) != dpkt.tcp.TCP and type(eth.data.data) != dpkt.udp.UDP:
            continue
        # 统计吞吐量
        if eth.data.data.dport in range(5201,5211):
            if eth.data.data.dport not in flows:
                flows[eth.data.data.dport] = 1
            if eth.data.data.dport not in bucket:
                bucket[eth.data.data.dport] = 0
            bucket[eth.data.data.dport] += len(buf)
    tuple([flows,buckets])
    if cache:
        with open("./{}-buckets-cache.pickle".format(alg),"wb") as f:
            pickle.dump((flows,buckets),f)
        with open("./{}-jain-cache.pickle".format(alg),"wb") as f:
            pickle.dump(jain,f)

def _read_algorithm_cache(alg):
    with open("./{}-buckets-cache.pickle".format(alg),"rb") as f:
        flows,buckets = pickle.load(f)
    return flows,buckets

def draw(ax,alg,alpha=0.3,color="r"):
    """
    :param ax: matplotlib ax object.
    :param alg: 算法名。根据算法名查询缓存（上一步处理 pcap 后生成）
    :param alpha: 绘制区域的透明度
    :param color: 区域颜色
    :return:
    """
    flows, buckets = _read_algorithm_cache(alg)
    timestamps = [x for x in buckets.keys()]
    timestamps.sort()
    start_time = timestamps[0]
    flows = [x for x in flows]
    flows.sort()
    mean_tpts = []
    std_tpts = []

    for ts in timestamps:
        # buckets[ts] like {5201: 404439, 5202: 173927}
        tputs = [8e-6 * buckets[ts][x] for x in buckets[ts]] # in Mbps
        mean_tpts.append(np.mean(tputs))
        std_tpts.append(np.std(tputs))
    timeline = [x-start_time for x in timestamps]
    mean_tpts = np.array(mean_tpts)
    std_tpts = np.array(std_tpts)

    ax.fill_between(timeline,mean_tpts-std_tpts,mean_tpts+std_tpts,alpha=alpha,color=color,linewidth=0.0,label=str(alg))
    ax.legend()
    ax.set_ylim(1,100)
    ax.set_yscale("log")
    ax.set_xlim(0,19) # Note! it depends on the time you set
    ax.xaxis.set_ticks(np.arange(1,20))
