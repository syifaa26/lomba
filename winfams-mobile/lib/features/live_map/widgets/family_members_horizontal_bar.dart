import 'package:flutter/material.dart';
import '../../../core/models/family_model.dart';
import '../../../core/theme/app_theme.dart';

/// Horizontal scrollable bar displaying family members and their monitoring roles.
class FamilyMembersHorizontalBar extends StatelessWidget {
  final List<FamilyMemberModel> members;
  final int? selectedMemberId;
  final ValueChanged<int>? onSelectMember;

  const FamilyMembersHorizontalBar({
    super.key,
    required this.members,
    this.selectedMemberId,
    this.onSelectMember,
  });

  @override
  Widget build(BuildContext context) {
    if (members.isEmpty) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 16),
        itemCount: members.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final member = members[index];
          final isSelected = member.id == selectedMemberId;

          return Semantics(
            button: true,
            label: 'Anggota ${member.name}, Peran ${member.role}',
            child: InkWell(
              borderRadius: BorderRadius.circular(24),
              onTap: () => onSelectMember?.call(member.id),
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                decoration: BoxDecoration(
                  color: isSelected ? AppTheme.accentCyan : AppTheme.surfaceDark,
                  borderRadius: BorderRadius.circular(24),
                  border: Border.all(
                    color: isSelected ? AppTheme.accentCyan : Colors.white24,
                  ),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    CircleAvatar(
                      radius: 12,
                      backgroundColor: isSelected
                          ? AppTheme.backgroundDark
                          : AppTheme.cardDark,
                      child: Text(
                        member.name.isNotEmpty
                            ? member.name[0].toUpperCase()
                            : 'M',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: isSelected ? AppTheme.accentCyan : Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    Text(
                      member.name,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: isSelected ? AppTheme.backgroundDark : Colors.white,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                      decoration: BoxDecoration(
                        color: member.role == 'DRIVER'
                            ? AppTheme.statusNormal.withValues(alpha: 0.2)
                            : Colors.grey.withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        member.role,
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: member.role == 'DRIVER'
                              ? AppTheme.statusNormal
                              : Colors.grey,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}
