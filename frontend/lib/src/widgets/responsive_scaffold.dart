import 'package:flutter/material.dart';

import '../core/responsive/breakpoints.dart';

class AdaptiveDestination {
  const AdaptiveDestination({
    required this.location,
    required this.label,
    required this.icon,
    required this.selectedIcon,
  });

  final String location;
  final String label;
  final IconData icon;
  final IconData selectedIcon;
}

class ResponsiveScaffold extends StatelessWidget {
  const ResponsiveScaffold({
    super.key,
    required this.body,
    required this.destinations,
    required this.currentLocation,
    required this.onDestinationSelected,
    this.appBar,
    this.floatingActionButton,
  });

  final Widget body;
  final List<AdaptiveDestination> destinations;
  final String currentLocation;
  final ValueChanged<AdaptiveDestination> onDestinationSelected;
  final PreferredSizeWidget? appBar;
  final Widget? floatingActionButton;

  int get _currentIndex {
    final index = destinations.indexWhere(
      (destination) => currentLocation.startsWith(destination.location),
    );
    return index >= 0 ? index : 0;
  }

  @override
  Widget build(BuildContext context) {
    final selectedIndex = _currentIndex;

    if (AppBreakpoints.isExpanded(context)) {
      return Scaffold(
        appBar: appBar,
        floatingActionButton: floatingActionButton,
        body: Row(
          children: <Widget>[
            NavigationRail(
              labelType: NavigationRailLabelType.all,
              selectedIndex: selectedIndex,
              onDestinationSelected: (index) => onDestinationSelected(destinations[index]),
              destinations: destinations
                  .map(
                    (destination) => NavigationRailDestination(
                      icon: Icon(destination.icon),
                      selectedIcon: Icon(destination.selectedIcon),
                      label: Text(destination.label),
                    ),
                  )
                  .toList(),
            ),
            const VerticalDivider(width: 1),
            Expanded(child: body),
          ],
        ),
      );
    }

    return Scaffold(
      appBar: appBar,
      floatingActionButton: floatingActionButton,
      body: body,
      bottomNavigationBar: NavigationBar(
        selectedIndex: selectedIndex,
        onDestinationSelected: (index) => onDestinationSelected(destinations[index]),
        destinations: destinations
            .map(
              (destination) => NavigationDestination(
                icon: Icon(destination.icon),
                selectedIcon: Icon(destination.selectedIcon),
                label: Text(destination.label),
              ),
            )
            .toList(),
      ),
    );
  }
}
