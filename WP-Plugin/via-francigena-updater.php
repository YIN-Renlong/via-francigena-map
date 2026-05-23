<?php
/**
 * Plugin Name: Via Francigena Map Updater
 * Description: 1-Click updater to pull the latest interactive map from GitHub to the /map directory.
 * Version: 1.1 (Upgraded with Cache Busting & Error Logging)
 * Author: YIN Renlong
 */

if ( ! defined( 'ABSPATH' ) ) exit; // Exit if accessed directly

// Global variable to store detailed copy errors
global $vfm_copy_errors;
$vfm_copy_errors = array();

// 1. Add the Button to the Top Admin Bar
add_action( 'admin_bar_menu', 'vfm_add_admin_bar_button', 100 );
function vfm_add_admin_bar_button( $admin_bar ) {
    if ( ! current_user_can( 'manage_options' ) ) return; 

    $admin_bar->add_node( array(
        'id'    => 'vfm-update-map',
        'title' => '🗺️ Update Francigena Map',
        'href'  => wp_nonce_url( admin_url( 'admin-post.php?action=vfm_update_map' ), 'vfm_update_nonce' ),
        'meta'  => array( 'title' => 'Pull latest version from GitHub' )
    ));
}

// 2. Handle the Button Click
add_action( 'admin_post_vfm_update_map', 'vfm_handle_update' );
function vfm_handle_update() {
    global $wp_filesystem, $vfm_copy_errors;

    if ( ! current_user_can( 'manage_options' ) || ! isset( $_GET['_wpnonce'] ) || ! wp_verify_nonce( $_GET['_wpnonce'], 'vfm_update_nonce' ) ) {
        wp_die( 'Security check failed.' );
    }

    require_once( ABSPATH . 'wp-admin/includes/file.php' );
    WP_Filesystem();

    // CACHE BUSTER: Forces GitHub to give us the absolute newest ZIP file, not a cached one!
    $github_zip_url = 'https://github.com/YIN-Renlong/via-francigena-map/archive/refs/heads/main.zip?nocache=' . time();
    $target_dir = ABSPATH . 'map'; 
    $temp_dir = WP_CONTENT_DIR . '/vfm_temp_extract'; 

    // Step A: Download the ZIP
    $tmp_zip = download_url( $github_zip_url );
    if ( is_wp_error( $tmp_zip ) ) {
        wp_redirect( admin_url( '?vfm_status=error_download' ) );
        exit;
    }

    // Step B: Unzip to temp folder
    $unzip_result = unzip_file( $tmp_zip, $temp_dir );
    unlink( $tmp_zip ); 

    if ( is_wp_error( $unzip_result ) ) {
        wp_redirect( admin_url( '?vfm_status=error_unzip' ) );
        exit;
    }

    // Step C: Move files to /map
    $source_dir = $temp_dir . '/via-francigena-map-main';
    
    if ( ! is_dir( $target_dir ) ) {
        wp_mkdir_p( $target_dir ); 
    }

    $copy_success = vfm_recursive_copy_and_filter( $source_dir, $target_dir );

    // Step D: Cleanup temp files
    $wp_filesystem->delete( $temp_dir, true );

    // Step E: Redirect with success or detailed error message
    if ( $copy_success ) {
        wp_redirect( admin_url( '?vfm_status=success' ) );
    } else {
        // Save the exact errors to a transient so we can display them on the next page load
        set_transient( 'vfm_copy_error_log', implode( '<br>', $vfm_copy_errors ), 60 );
        wp_redirect( admin_url( '?vfm_status=error_copy' ) );
    }
    exit;
}

// 3. Custom Copy Function with Error Logging
function vfm_recursive_copy_and_filter( $src, $dst ) {
    global $vfm_copy_errors;
    $dir = opendir( $src );
    @mkdir( $dst, 0755, true );
    $success = true;

    while ( false !== ( $file = readdir( $dir ) ) ) {
        if ( ( $file != '.' ) && ( $file != '..' ) ) {
            
            // Ignore Python files & backend data
            $blacklist = array( 'kml_raw', '.github', '.gitignore', 'README.md' );
            if ( in_array( $file, $blacklist ) ) continue;
            if ( pathinfo( $file, PATHINFO_EXTENSION ) === 'py' ) continue;

            if ( is_dir( $src . '/' . $file ) ) {
                $res = vfm_recursive_copy_and_filter( $src . '/' . $file, $dst . '/' . $file );
                if ( !$res ) $success = false;
            } else {
                // Try to delete the old file first to prevent overwrite permission errors
                if ( file_exists( $dst . '/' . $file ) ) {
                    @unlink( $dst . '/' . $file );
                }
                
                $res = copy( $src . '/' . $file, $dst . '/' . $file );
                if ( !$res ) {
                    $success = false;
                    $vfm_copy_errors[] = "Failed to copy: " . $dst . '/' . $file; // Log the exact file!
                }
            }
        }
    }
    closedir( $dir );
    return $success;
}

// 4. Show the Notification Message on Screen
add_action( 'admin_notices', 'vfm_admin_notices' );
function vfm_admin_notices() {
    if ( ! isset( $_GET['vfm_status'] ) ) return;

    $status = $_GET['vfm_status'];
    
    if ( $status === 'success' ) {
        echo '<div class="notice notice-success is-dismissible"><p>✅ <strong>Success!</strong> The Via Francigena map was successfully updated from GitHub. <a href="/map/" target="_blank">View Map</a></p></div>';
    } elseif ( $status === 'error_download' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not download the ZIP file from GitHub.</p></div>';
    } elseif ( $status === 'error_unzip' ) {
        echo '<div class="notice notice-error is-dismissible"><p>❌ <strong>Error:</strong> Could not unzip the file. Check server permissions.</p></div>';
    } elseif ( $status === 'error_copy' ) {
        $error_log = get_transient( 'vfm_copy_error_log' );
        echo '<div class="notice notice-error is-dismissible">';
        echo '<p>⚠️ <strong>Warning:</strong> Some files could not be copied to the /map directory due to server write permissions.</p>';
        if ( $error_log ) {
            echo '<p><strong>Details:</strong><br>' . $error_log . '</p>';
        }
        echo '</div>';
        delete_transient( 'vfm_copy_error_log' );
    }
}
?>