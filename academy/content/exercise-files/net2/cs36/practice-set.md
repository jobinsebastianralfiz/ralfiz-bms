# Practice set: File systems and I/O (UGC NET Paper 2, Unit 5)

Time: 22 minutes. For every scheduling problem, sort the queue and mark the head on a number line first.

## Data for problems 1–4
Cylinders 0–499. Head at 250, moving towards cylinder 0. Queue: 310, 95, 420, 180, 40, 275, 490, 130.

**1.** Total head movement for FCFS and SSTF.

**2.** Total head movement for SCAN and LOOK.

**3.** Total head movement for C-SCAN (after reaching 0, jump to 499 and continue downwards), both counting and not counting the jump.

**4.** Total head movement for C-LOOK, both counting and not counting the jump.

**5.** An inode has 10 direct pointers and single, double and triple indirect pointers. Blocks are 1 KB and pointers are 4 bytes. What is the maximum file size in KB?

**6.** For the inode of problem 5 (inode in memory), how many disk reads does it take to read the data block holding byte offset 300,000?

**7.** A disk has 8 surfaces, 4,096 tracks per surface, 512 sectors per track and 512 bytes per sector. Find the capacity and the number of bits in a sector address.

**8.** A 15,000 RPM disk has an average seek of 3.5 ms. Find the average time to read one 4 KB block if the transfer rate is 100 MB/s (take 1 MB = 10^6 bytes).

**9.** A 2 TB disk (2^41 bytes) uses 8 KB blocks. Find the size of the bit vector.

**10.** Five 3 TB disks: find the usable capacity for RAID 0, RAID 1+0 (use four disks), RAID 5 and RAID 6.

**11.** Match List I with List II.

| List I | List II |
|---|---|
| A. Contiguous | I. Index block |
| B. Linked | II. External fragmentation |
| C. Indexed | III. FAT is a variant |
| D. Bit vector | IV. Free-space management |

(1) A-II, B-III, C-I, D-IV (2) A-III, B-II, C-I, D-IV (3) A-II, B-I, C-III, D-IV (4) A-II, B-III, C-IV, D-I

**12.** Assertion (A): SSTF may starve a request. Reason (R): SSTF is a form of SJF scheduling applied to disk requests.
(1) Both true, R explains A (2) Both true, R does not explain A (3) A true, R false (4) A false, R true

**13.** Statement I: RAID 6 needs at least four disks. Statement II: RAID 1 doubles the usable capacity.
(1) Both true (2) Both false (3) I true, II false (4) I false, II true

**14.** Which are correct? A. LOOK never gives more head movement than SCAN in the same direction. B. FCFS can starve requests. C. C-SCAN treats the disk as circular. D. Spooling suits printers. E. A symbolic link stores the target's inode number.
(1) A, C and D only (2) A, B and C only (3) C and D only (4) A, C, D and E only

**15.** Free-space bitmap (1 = free), 8-bit words: 00000000 00000000 00000000 00000000 00100110. Find the first free block.
