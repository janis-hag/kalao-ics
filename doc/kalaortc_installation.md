
## Getting the kernel source and configure
```bash
mkdir rt_kernel
git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
git checkout tags/v5.15.31
cp ~/kalao-ics/kalao-config/RT_kernel_config rt_kernel/.config
```
Apply patch: patch-5.15.31-rt38.patch.xz

## Building the kernel
```bash
make clean
rm vmlinux-gdb.py
rm -r debian/
make -j `getconf _NPROCESSORS_ONLN` deb-pkg LOCALVERSION=-kalaortc-5
```

Edit kernel cmdline in /etc/default/grub
```bash
GRUB_CMDLINE_LINUX_DEFAULT="i915.force_probe=4c8a isolcpus=5-7 nohz_full=5-7 nohz=on rcu_nocbs=5-7 no_stf_barrier mds=off mitigations=off earlyprintk=efi,keep"
update-grub
```
