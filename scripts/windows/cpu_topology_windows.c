#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <stdlib.h>

int main(void) {
    PSYSTEM_CPU_SET_INFORMATION info = NULL;
    ULONG length = 0, offset = 0;
    if (GetSystemCpuSetInformation(NULL, 0, &length, GetCurrentProcess(), 0) ||
        GetLastError() != ERROR_INSUFFICIENT_BUFFER || length == 0) {
        fprintf(stderr, "GetSystemCpuSetInformation size query failed: %lu\n", GetLastError());
        return 1;
    }
    info = (PSYSTEM_CPU_SET_INFORMATION)malloc(length);
    if (!info) return 1;
    if (!GetSystemCpuSetInformation(info, length, &length, GetCurrentProcess(), 0)) {
        fprintf(stderr, "GetSystemCpuSetInformation query failed: %lu\n", GetLastError());
        free(info);
        return 1;
    }
    while (offset < length) {
        PSYSTEM_CPU_SET_INFORMATION row = (PSYSTEM_CPU_SET_INFORMATION)((BYTE *)info + offset);
        if (row->Type == CpuSetInformation) {
            printf("CPUSET\tid=%lu\tgroup=%u\tlogical_processor=%u\tcore=%u\tefficiency_class=%u\tparked=%u\tallocated=%u\n",
                   row->CpuSet.Id, row->CpuSet.Group, row->CpuSet.LogicalProcessorIndex,
                   row->CpuSet.CoreIndex, row->CpuSet.EfficiencyClass, row->CpuSet.Parked,
                   row->CpuSet.Allocated);
        }
        if (row->Size == 0) break;
        offset += row->Size;
    }
    free(info);
    return 0;
}
