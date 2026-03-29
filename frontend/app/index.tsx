import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
  Modal,
  Dimensions,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';

const EXPO_PUBLIC_BACKEND_URL = process.env.EXPO_PUBLIC_BACKEND_URL;
const API_BASE_URL = `${EXPO_PUBLIC_BACKEND_URL}/api`;

const { width } = Dimensions.get('window');
const isMobile = width < 768;

// Database configuration
const DATABASES = [
  { key: 'neondb', name: 'LDB App Users', priority: true, hasInactive: true },
  { key: 'idpass', name: 'IDPass Users', priority: true, hasInactive: false },
  { key: 'pmfby', name: 'PMFBY Users', priority: false, hasInactive: false },
  { key: 'krp', name: 'KRP Users', priority: false, hasInactive: false },
  { key: 'byajanudan', name: 'Byaj Anudan Users', priority: false, hasInactive: false },
];

interface ToastMessage {
  message: string;
  type: 'success' | 'error';
}

export default function AdminPanel() {
  const [selectedDb, setSelectedDb] = useState('neondb');
  const [activeTab, setActiveTab] = useState('pending');
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [counts, setCounts] = useState<any>({});
  const [toast, setToast] = useState<ToastMessage | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(!isMobile);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    fetchCounts();
  }, []);

  useEffect(() => {
    fetchData();
  }, [selectedDb, activeTab]);

  const fetchCounts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/counts`);
      if (response.data.success) {
        setCounts(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching counts:', error);
    }
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      let endpoint = '';
      if (activeTab === 'pending') {
        endpoint = `${API_BASE_URL}/${selectedDb}/pending`;
      } else if (activeTab === 'approved') {
        endpoint = `${API_BASE_URL}/${selectedDb}/approved`;
      } else if (activeTab === 'inactive' && selectedDb === 'neondb') {
        endpoint = `${API_BASE_URL}/neondb/inactive`;
      }

      const response = await axios.get(endpoint);
      if (response.data.success) {
        setData(response.data.data || []);
      }
    } catch (error: any) {
      showToast('Error loading data: ' + error.message, 'error');
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchData();
    await fetchCounts();
    setRefreshing(false);
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const confirmAction = (
    title: string,
    message: string,
    sr: number,
    onConfirm: () => Promise<void>
  ) => {
    Alert.alert(
      title,
      message,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          onPress: () => {
            // Set loading immediately
            setActionLoading(sr);
            // Execute async operation
            onConfirm()
              .catch((error) => {
                console.error('Confirmation action failed:', error);
                showToast('Operation failed: ' + (error.message || 'Unknown error'), 'error');
              })
              .finally(() => {
                setActionLoading(null);
              });
          },
          style: 'destructive',
        },
      ],
      { cancelable: true }
    );
  };

  const handleApprove = async (sr: number) => {
    setActionLoading(sr);
    try {
      console.log('Approving SR:', sr, 'DB:', selectedDb, 'URL:', `${API_BASE_URL}/${selectedDb}/approve/${sr}`);
      const response = await axios.post(`${API_BASE_URL}/${selectedDb}/approve/${sr}`);
      console.log('Approve response:', response.data);
      if (response.data.success) {
        showToast('✅ Approved successfully!', 'success');
        await fetchData();
        await fetchCounts();
      } else {
        showToast('❌ Failed to approve', 'error');
      }
    } catch (error: any) {
      console.error('Approve error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Network error';
      showToast('❌ Error: ' + errorMsg, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (sr: number) => {
    confirmAction('Reject User', 'Are you sure you want to reject this user?', sr, async () => {
      try {
        console.log('Rejecting SR:', sr);
        const response = await axios.post(`${API_BASE_URL}/${selectedDb}/reject/${sr}`);
        console.log('Reject response:', response.data);
        if (response.data.success) {
          showToast('✅ Rejected successfully!', 'success');
          await fetchData();
          await fetchCounts();
        }
      } catch (error: any) {
        console.error('Reject error:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Network error';
        throw new Error(errorMsg);
      }
    });
  };

  const handleDeactivate = async (sr: number) => {
    confirmAction('Deactivate User', 'Move this user back to pending?', sr, async () => {
      try {
        console.log('Deactivating SR:', sr);
        const response = await axios.post(`${API_BASE_URL}/${selectedDb}/deactivate/${sr}`);
        console.log('Deactivate response:', response.data);
        if (response.data.success) {
          showToast('✅ Deactivated successfully!', 'success');
          await fetchData();
          await fetchCounts();
        }
      } catch (error: any) {
        console.error('Deactivate error:', error);
        const errorMsg = error.response?.data?.detail || error.message || 'Network error';
        throw new Error(errorMsg);
      }
    });
  };

  const handleDelete = async (sr: number) => {
    confirmAction(
      'Permanent Delete',
      'This will permanently delete the user. This action cannot be undone!',
      sr,
      async () => {
        try {
          console.log('Deleting SR:', sr);
          const response = await axios.delete(`${API_BASE_URL}/${selectedDb}/delete/${sr}`);
          console.log('Delete response:', response.data);
          if (response.data.success) {
            showToast('✅ Deleted permanently!', 'success');
            await fetchData();
            await fetchCounts();
          }
        } catch (error: any) {
          console.error('Delete error:', error);
          const errorMsg = error.response?.data?.detail || error.message || 'Network error';
          throw new Error(errorMsg);
        }
      }
    );
  };

  const handleReactivate = async (sr: number) => {
    setActionLoading(sr);
    try {
      console.log('Reactivating SR:', sr);
      const response = await axios.post(`${API_BASE_URL}/neondb/reactivate/${sr}`);
      console.log('Reactivate response:', response.data);
      if (response.data.success) {
        showToast('✅ Reactivated successfully!', 'success');
        await fetchData();
        await fetchCounts();
      }
    } catch (error: any) {
      console.error('Reactivate error:', error);
      const errorMsg = error.response?.data?.detail || error.message || 'Network error';
      showToast('❌ Error: ' + errorMsg, 'error');
    } finally {
      setActionLoading(null);
    }
  };

  const renderSidebar = () => (
    <View style={[styles.sidebar, !sidebarOpen && isMobile && styles.sidebarHidden]}>
      <View style={styles.sidebarHeader}>
        <Text style={styles.sidebarTitle}>Admin Panel</Text>
        {isMobile && (
          <TouchableOpacity onPress={() => setSidebarOpen(false)}>
            <Text style={styles.closeButton}>✕</Text>
          </TouchableOpacity>
        )}
      </View>

      <ScrollView style={styles.dbList}>
        {DATABASES.map((db) => (
          <View key={db.key} style={styles.dbSection}>
            <TouchableOpacity
              style={[styles.dbButton, selectedDb === db.key && styles.dbButtonActive]}
              onPress={() => {
                setSelectedDb(db.key);
                setActiveTab('pending');
                if (isMobile) setSidebarOpen(false);
              }}
            >
              <Text style={styles.dbName}>
                {db.priority && '⭐ '}
                {db.name}
              </Text>
            </TouchableOpacity>

            {selectedDb === db.key && (
              <View style={styles.tabsContainer}>
                <TouchableOpacity
                  style={[styles.tab, activeTab === 'pending' && styles.tabActive]}
                  onPress={() => setActiveTab('pending')}
                >
                  <Text style={styles.tabText}>Pending</Text>
                  <View style={[styles.badge, styles.badgeAmber]}>
                    <Text style={styles.badgeText}>{counts[db.key]?.pending || 0}</Text>
                  </View>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.tab, activeTab === 'approved' && styles.tabActive]}
                  onPress={() => setActiveTab('approved')}
                >
                  <Text style={styles.tabText}>
                    {db.key === 'neondb' ? 'Active' : 'Approved'}
                  </Text>
                  <View style={[styles.badge, styles.badgeGreen]}>
                    <Text style={styles.badgeText}>{counts[db.key]?.approved || 0}</Text>
                  </View>
                </TouchableOpacity>

                {db.hasInactive && (
                  <TouchableOpacity
                    style={[styles.tab, activeTab === 'inactive' && styles.tabActive]}
                    onPress={() => setActiveTab('inactive')}
                  >
                    <Text style={styles.tabText}>Inactive</Text>
                    <View style={[styles.badge, styles.badgeRed]}>
                      <Text style={styles.badgeText}>{counts[db.key]?.inactive || 0}</Text>
                    </View>
                  </TouchableOpacity>
                )}
              </View>
            )}
          </View>
        ))}
      </ScrollView>
    </View>
  );

  const renderTableRow = (item: any) => {
    const isNeonDb = selectedDb === 'neondb';
    const userIdField = selectedDb === 'idpass' ? 'user_name' : 'user_id';

    return (
      <View key={item.sr} style={styles.tableRow}>
        <ScrollView horizontal showsHorizontalScrollIndicator={true}>
          <View style={styles.rowContent}>
            <View style={styles.cell}>
              <Text style={styles.cellLabel}>SR</Text>
              <Text style={styles.cellValue}>{item.sr}</Text>
            </View>

            {isNeonDb ? (
              <>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>User ID</Text>
                  <Text style={styles.cellValue}>{item.userid || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>PACS Name</Text>
                  <Text style={styles.cellValue}>{item.pacs_name || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Created On</Text>
                  <Text style={styles.cellValue}>
                    {item.created_on
                      ? new Date(item.created_on).toLocaleDateString()
                      : item.approved_on
                      ? new Date(item.approved_on).toLocaleDateString()
                      : '-'}
                  </Text>
                </View>
              </>
            ) : (
              <>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>
                    {selectedDb === 'idpass' ? 'User Name' : 'User ID'}
                  </Text>
                  <Text style={styles.cellValue}>{item[userIdField] || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Name</Text>
                  <Text style={styles.cellValue}>{item.name || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>PACS</Text>
                  <Text style={styles.cellValue}>{item.pacs_name || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Branch</Text>
                  <Text style={styles.cellValue}>{item.branch || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>District</Text>
                  <Text style={styles.cellValue}>{item.dist || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>State</Text>
                  <Text style={styles.cellValue}>{item.state || '-'}</Text>
                </View>
                <View style={styles.cell}>
                  <Text style={styles.cellLabel}>Mobile</Text>
                  <Text style={styles.cellValue}>{item.mobile || '-'}</Text>
                </View>
              </>
            )}

            <View style={styles.actionsCell}>
              {activeTab === 'pending' && (
                <>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonApprove, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleApprove(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Approve</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonReject, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleReject(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Reject</Text>
                    )}
                  </TouchableOpacity>
                </>
              )}

              {activeTab === 'approved' && (
                <>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonDeactivate, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleDeactivate(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Deactivate</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonDelete, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleDelete(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Delete</Text>
                    )}
                  </TouchableOpacity>
                </>
              )}

              {activeTab === 'inactive' && isNeonDb && (
                <>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonReactivate, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleReactivate(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Reactivate</Text>
                    )}
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.button, styles.buttonDelete, actionLoading === item.sr && styles.buttonDisabled]}
                    onPress={() => handleDelete(item.sr)}
                    disabled={actionLoading === item.sr}
                  >
                    {actionLoading === item.sr ? (
                      <ActivityIndicator size="small" color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Delete</Text>
                    )}
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        </ScrollView>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      {isMobile && !sidebarOpen && (
        <TouchableOpacity
          style={styles.menuButton}
          onPress={() => setSidebarOpen(true)}
        >
          <Text style={styles.menuIcon}>☰</Text>
        </TouchableOpacity>
      )}

      <View style={styles.mainContainer}>
        {renderSidebar()}

        <View style={styles.content}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>
              {DATABASES.find((db) => db.key === selectedDb)?.name} -{' '}
              {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
            </Text>
            <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
              <Text style={styles.refreshIcon}>↻</Text>
            </TouchableOpacity>
          </View>

          {loading ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#3b82f6" />
              <Text style={styles.loadingText}>Loading...</Text>
            </View>
          ) : (
            <ScrollView
              style={styles.tableContainer}
              refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
              }
            >
              {data.length === 0 ? (
                <View style={styles.emptyState}>
                  <Text style={styles.emptyText}>No records found</Text>
                </View>
              ) : (
                data.map(renderTableRow)
              )}
            </ScrollView>
          )}
        </View>
      </View>

      {toast && (
        <View
          style={[
            styles.toast,
            toast.type === 'success' ? styles.toastSuccess : styles.toastError,
          ]}
        >
          <Text style={styles.toastText}>{toast.message}</Text>
        </View>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f3f4f6',
  },
  mainContainer: {
    flex: 1,
    flexDirection: 'row',
  },
  menuButton: {
    position: 'absolute',
    top: 10,
    left: 10,
    zIndex: 1000,
    backgroundColor: '#1a1a2e',
    padding: 12,
    borderRadius: 8,
  },
  menuIcon: {
    fontSize: 24,
    color: '#fff',
  },
  sidebar: {
    width: isMobile ? '80%' : 280,
    backgroundColor: '#1a1a2e',
    borderRightWidth: 1,
    borderRightColor: '#2d2d44',
    ...(isMobile && {
      position: 'absolute',
      left: 0,
      top: 0,
      bottom: 0,
      zIndex: 999,
    }),
  },
  sidebarHidden: {
    left: -1000,
  },
  sidebarHeader: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#2d2d44',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sidebarTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#fff',
  },
  closeButton: {
    fontSize: 24,
    color: '#fff',
  },
  dbList: {
    flex: 1,
  },
  dbSection: {
    marginBottom: 8,
  },
  dbButton: {
    padding: 16,
    borderLeftWidth: 4,
    borderLeftColor: 'transparent',
  },
  dbButtonActive: {
    backgroundColor: '#2d2d44',
    borderLeftColor: '#3b82f6',
  },
  dbName: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
  tabsContainer: {
    paddingLeft: 16,
    paddingBottom: 8,
  },
  tab: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
    marginVertical: 2,
    borderRadius: 6,
  },
  tabActive: {
    backgroundColor: '#3b82f6',
  },
  tabText: {
    color: '#d1d5db',
    fontSize: 14,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
    minWidth: 24,
    alignItems: 'center',
  },
  badgeAmber: {
    backgroundColor: '#f59e0b',
  },
  badgeGreen: {
    backgroundColor: '#10b981',
  },
  badgeRed: {
    backgroundColor: '#ef4444',
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1f2937',
    flex: 1,
  },
  refreshButton: {
    padding: 8,
  },
  refreshIcon: {
    fontSize: 24,
    color: '#3b82f6',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  loadingText: {
    marginTop: 12,
    color: '#6b7280',
    fontSize: 16,
  },
  tableContainer: {
    flex: 1,
  },
  tableRow: {
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
    backgroundColor: '#fff',
  },
  rowContent: {
    flexDirection: 'row',
    padding: 16,
    minWidth: '100%',
  },
  cell: {
    marginRight: 24,
    minWidth: 120,
  },
  cellLabel: {
    fontSize: 12,
    color: '#6b7280',
    marginBottom: 4,
    fontWeight: '600',
  },
  cellValue: {
    fontSize: 14,
    color: '#1f2937',
  },
  actionsCell: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginLeft: 16,
  },
  button: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 6,
    marginHorizontal: 4,
  },
  buttonApprove: {
    backgroundColor: '#10b981',
  },
  buttonReject: {
    backgroundColor: '#ef4444',
  },
  buttonDeactivate: {
    backgroundColor: '#f59e0b',
  },
  buttonDelete: {
    backgroundColor: '#991b1b',
  },
  buttonReactivate: {
    backgroundColor: '#3b82f6',
  },
  buttonDisabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  emptyState: {
    padding: 40,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#6b7280',
  },
  toast: {
    position: 'absolute',
    bottom: 20,
    left: 20,
    right: 20,
    padding: 16,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  toastSuccess: {
    backgroundColor: '#10b981',
  },
  toastError: {
    backgroundColor: '#ef4444',
  },
  toastText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '600',
  },
});
