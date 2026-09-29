import React, { useEffect, useState } from 'react';
import { Users, UserPlus, Trash2, Loader2, Mail, Shield, X } from 'lucide-react';
import { toast } from 'sonner';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';
import { Link } from 'react-router-dom';

export default function TeamPage() {
  const { user } = useAuth();

  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [hasMultiUser, setHasMultiUser] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
  });

  const isOwner = user?.role === 'owner' || user?.role === 'business_owner';

  const fetchMembers = async () => {
  try {
    setLoading(true);

    // First check current plan entitlement.
    const entitlementResponse = await api.get('/auth/entitlements');

    const features =
      entitlementResponse?.data?.entitlements?.features ||
      entitlementResponse?.data?.features ||
      {};

    const multiUserEnabled = features.multi_user === true;

    setHasMultiUser(multiUserEnabled);

    // Normal Vyastha plan does not have Team & Staff.
    if (!multiUserEnabled) {
      toast.error(
        'Team & Staff is a Pro feature. Upgrade to Vyastha Pro to use it.'
      );
      setMembers([]);
      return;
    }

    // Only call the team API when the feature is available.
    const response = await api.get('/team/members');

    setMembers(
      Array.isArray(response.data)
        ? response.data
        : []
    );
  } catch (error) {
    const detail = error?.response?.data?.detail;

    const message =
      typeof detail === 'string'
        ? detail
        : 'Unable to load team members.';

    toast.error(message);
    setMembers([]);
  } finally {
    setLoading(false);
  }
};

  useEffect(() => {
  fetchMembers();
}, []);

 if (hasMultiUser === null) {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="flex items-center text-slate-500">
        <Loader2 size={20} className="animate-spin mr-2" />
        Checking your plan...
      </div>
    </div>
  );
}

if (hasMultiUser === false) {
  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="max-w-md w-full bg-white border border-slate-200 rounded-2xl shadow-sm p-8 text-center">
        <div className="mx-auto h-14 w-14 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
          <Users size={26} />
        </div>

        <h2 className="mt-5 text-xl font-bold text-slate-900">
          Team & Staff is a Pro Feature
        </h2>

        <p className="mt-2 text-sm text-slate-500 leading-6">
          Team management is available in Vyastha Pro.
          Upgrade your plan to add and manage staff members.
        </p>

        <Link
  to="/subscription"
  className="mt-6 inline-flex items-center justify-center px-5 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors"
>
  Upgrade to Pro
</Link>
      </div>
    </div>
  );
}

const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleAddStaff = async (event) => {
    event.preventDefault();

    if (!form.name.trim() || !form.email.trim() || !form.password) {
      toast.error('Please fill all fields.');
      return;
    }

    try {
      setSaving(true);

      await api.post('/team/members', {
        name: form.name.trim(),
        email: form.email.trim(),
        password: form.password,
      });

      toast.success('Staff member added successfully.');

      setForm({
        name: '',
        email: '',
        password: '',
      });

      setShowAddForm(false);
      await fetchMembers();
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        'Unable to add staff member.';

      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (member) => {
    if (!window.confirm(`Remove ${member.name} from your team?`)) {
      return;
    }

    try {
      setDeletingId(member.id);

      await api.delete(`/team/members/${member.id}`);

      toast.success('Team member removed successfully.');

      await fetchMembers();
    } catch (error) {
      const message =
        error?.response?.data?.detail ||
        'Unable to remove team member.';

      toast.error(message);
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <div className="p-2.5 bg-blue-100 text-blue-600 rounded-xl">
              <Users size={22} />
            </div>

            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Team & Staff
              </h1>

              <p className="text-sm text-slate-500 mt-1">
                Manage your business team members.
              </p>
            </div>
          </div>
        </div>

        {isOwner && (
          <button
            type="button"
            onClick={() => setShowAddForm(true)}
            className="inline-flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors shadow-sm"
          >
            <UserPlus size={17} />
            Add Staff
          </button>
        )}
      </div>

      {/* Add Staff Form */}
      {showAddForm && isOwner && (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm p-5">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h2 className="text-base font-bold text-slate-900">
                Add Team Member
              </h2>

              <p className="text-sm text-slate-500 mt-1">
                Create login credentials for a staff member.
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowAddForm(false)}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg"
            >
              <X size={18} />
            </button>
          </div>

          <form
            onSubmit={handleAddStaff}
            className="grid grid-cols-1 md:grid-cols-3 gap-4"
          >
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Staff Name
              </label>

              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Rahul Sharma"
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Email
              </label>

              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleChange}
                placeholder="staff@example.com"
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5">
                Password
              </label>

              <input
                type="password"
                name="password"
                value={form.password}
                onChange={handleChange}
                placeholder="Minimum 6 characters"
                minLength={6}
                className="w-full px-3 py-2.5 border border-slate-300 rounded-lg text-sm outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>

            <div className="md:col-span-3 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-4 py-2.5 border border-slate-300 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-50"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={saving}
                className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {saving && <Loader2 size={16} className="animate-spin" />}
                {saving ? 'Adding...' : 'Add Staff'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Team Members */}
      <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between">
          <div>
            <h2 className="font-bold text-slate-900">
              Team Members
            </h2>

            <p className="text-xs text-slate-500 mt-1">
              {members.length} member{members.length !== 1 ? 's' : ''} in this business
            </p>
          </div>

          <div className="p-2 bg-slate-100 rounded-lg text-slate-500">
            <Users size={18} />
          </div>
        </div>

        {loading ? (
          <div className="py-12 flex items-center justify-center text-slate-500">
            <Loader2 size={20} className="animate-spin mr-2" />
            Loading team members...
          </div>
        ) : members.length === 0 ? (
          <div className="py-12 text-center">
            <Users size={36} className="mx-auto text-slate-300" />

            <p className="mt-3 text-sm font-medium text-slate-700">
              No team members found
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Add a staff member to start building your team.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {members.map((member) => {
              const isCurrentUser = member.id === user?.id;
              const isMemberOwner =
                member.role === 'owner' ||
                member.role === 'business_owner';

              return (
                <div
                  key={member.id}
                  className="px-5 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-sm">
                      {(member.name || member.email || '?')
                        .charAt(0)
                        .toUpperCase()}
                    </div>

                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-slate-900">
                          {member.name}
                        </p>

                        {isCurrentUser && (
                          <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200 font-semibold">
                            You
                          </span>
                        )}
                      </div>

                      <div className="flex items-center gap-1.5 mt-1 text-xs text-slate-500">
                        <Mail size={13} />
                        {member.email}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 text-xs font-medium">
                      <Shield size={13} />
                      {isMemberOwner ? 'Owner' : 'Staff'}
                    </span>

                    {isOwner && !isMemberOwner && (
                      <button
                        type="button"
                        onClick={() => handleDelete(member)}
                        disabled={deletingId === member.id}
                        className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-red-600 border border-red-200 rounded-lg hover:bg-red-50 disabled:opacity-50"
                      >
                        {deletingId === member.id ? (
                          <Loader2 size={14} className="animate-spin" />
                        ) : (
                          <Trash2 size={14} />
                        )}
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}