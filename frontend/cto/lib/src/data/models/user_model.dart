class UserModel {
  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    this.avatar,
  });

  final String id;
  final String name;
  final String email;
  final String? avatar;

  factory UserModel.fromJson(Map<String, dynamic> json) {
    return UserModel(
      id: json['id'] as String,
      name: json['name'] as String,
      email: json['email'] as String,
      avatar: json['avatar'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return <String, dynamic>{
      'id': id,
      'name': name,
      'email': email,
      if (avatar != null) 'avatar': avatar,
    };
  }

  UserModel copyWith({
    String? id,
    String? name,
    String? email,
    String? avatar,
  }) {
    return UserModel(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      avatar: avatar ?? this.avatar,
    );
  }
}
