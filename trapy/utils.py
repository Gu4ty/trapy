from struct import unpack

def parse_address(address):
    host, port = address.split(':')

    if host == '':
        host = 'localhost'

    return host, int(port)



def checksum(packet):
    total = 0

    # Add up 16-bit words
    num_words = len(packet) // 2
    for chunk in unpack("!%sH" % num_words, packet[0:num_words * 2]):
        total += chunk

    # Add any left over byte
    if len(packet) % 2:
        total += packet[-1] << 8

    # Fold 32-bits into 16-bits
    total = (total >> 16) + (total & 0xffff)
    total += total >> 16
    return ~total + 0x10000 & 0xffff 


def update_rtt(estimated_rtt, sample_rtt):
        estimated_rtt = 0.875 * estimated_rtt + 0.125 * sample_rtt
        dev_rtt =  0.25 * abs(sample_rtt - estimated_rtt)
        timeout_interval = estimated_rtt + 4 * dev_rtt
        return timeout_interval, estimated_rtt

